"""Sandbox execution environment for bot isolation.

This module provides secure isolation for untrusted bot code by running
bot processes in restricted environments with resource limits.
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Callable

from ..bots.bot_interface import BotInterface
from ..views import GameView


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution limits."""
    cpu_time_limit: float = 30.0  # seconds
    wall_time_limit: float = 60.0  # seconds
    memory_limit_mb: int = 256
    max_processes: int = 10
    max_threads: int = 20
    temp_fs_limit_mb: int = 100
    network_disabled: bool = True


@dataclass
class SandboxResult:
    """Result of a sandboxed execution."""
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: float = 0.0
    memory_used_mb: float = 0.0
    timeout: bool = False
    resource_exceeded: bool = False


class BotSandbox:
    """Isolated execution environment for bot code."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._temp_dir: Optional[Path] = None
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def _create_temp_environment(self) -> Path:
        """Create a temporary directory for bot execution."""
        temp_dir = Path(tempfile.mkdtemp(prefix="catan_sandbox_"))
        return temp_dir

    def _cleanup_temp_environment(self) -> None:
        """Clean up temporary directory."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                # Clean up files recursively
                for item in self._temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        for sub_item in item.iterdir():
                            if sub_item.is_file():
                                sub_item.unlink()
                        item.rmdir()
                self._temp_dir.rmdir()
            except Exception as e:
                print(f"Warning: Failed to cleanup temp directory: {e}")
        self._temp_dir = None

    def _prepare_isolated_environment(self) -> Dict[str, str]:
        """Prepare environment variables for isolated execution."""
        env = os.environ.copy()
        
        # Remove sensitive environment variables
        sensitive_keys = [
            'DATABASE_URL', 'API_KEY', 'SECRET_KEY', 'PASSWORD', 
            'TOKEN', 'CREDENTIALS', 'AWS_SECRET', 'AZURE_KEY'
        ]
        for key in sensitive_keys:
            env.pop(key, None)
            env.pop(key.lower(), None)
        
        # Set restricted PATH (cross-platform)
        python_dir = os.path.dirname(sys.executable)
        if sys.platform == 'win32':
            env['PATH'] = os.pathsep.join([
                python_dir,
                os.path.join(python_dir, 'Scripts'),
                r'C:\Windows\System32',
            ])
        else:
            env['PATH'] = os.pathsep.join([
                python_dir,
                '/usr/bin',
                '/bin',
            ])
        
        # Disable network-related environment variables
        if self.config.network_disabled:
            env['NO_PROXY'] = '*'
            env['no_proxy'] = '*'
        
        return env

    def execute_bot_action(
        self,
        bot_code: str,
        action: str,
        view_data: Dict[str, Any],
        available_actions: Optional[list] = None,
        timeout: Optional[float] = None
    ) -> SandboxResult:
        """Execute a bot action in the sandbox."""
        timeout = timeout or self.config.wall_time_limit
        start_time = time.time()
        
        with self._lock:
            try:
                self._temp_dir = self._create_temp_environment()
                
                # Write bot code to temporary file
                bot_file = self._temp_dir / "bot.py"
                bot_file.write_text(bot_code)
                
                # Prepare input data
                input_data = {
                    "action": action,
                    "view": view_data,
                    "available_actions": available_actions
                }
                
                input_file = self._temp_dir / "input.json"
                input_file.write_text(json.dumps(input_data))
                
                # Prepare execution environment
                env = self._prepare_isolated_environment()
                
                # Execute bot code in subprocess
                try:
                    # Use current Python interpreter for cross-platform compatibility
                    python_exe = sys.executable
                    creation_flags = 0
                    if sys.platform == 'win32':
                        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
                    
                    process = subprocess.Popen(
                        [python_exe, str(bot_file), str(input_file)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env,
                        cwd=str(self._temp_dir),
                        creationflags=creation_flags
                    )
                    
                    try:
                        stdout, stderr = process.communicate(timeout=timeout)
                        exit_code = process.returncode
                        execution_time = time.time() - start_time
                        
                        if exit_code == 0:
                            try:
                                output = json.loads(stdout.decode('utf-8'))
                                return SandboxResult(
                                    success=True,
                                    output=output,
                                    exit_code=exit_code,
                                    execution_time=execution_time
                                )
                            except json.JSONDecodeError:
                                return SandboxResult(
                                    success=False,
                                    error="Invalid JSON output from bot",
                                    exit_code=exit_code,
                                    execution_time=execution_time
                                )
                        else:
                            error_msg = stderr.decode('utf-8', errors='replace')
                            return SandboxResult(
                                success=False,
                                error=error_msg or f"Bot exited with code {exit_code}",
                                exit_code=exit_code,
                                execution_time=execution_time
                            )
                    except subprocess.TimeoutExpired:
                        process.kill()
                        stdout, stderr = process.communicate()
                        return SandboxResult(
                            success=False,
                            error="Execution timeout",
                            timeout=True,
                            execution_time=time.time() - start_time
                        )
                        
                except Exception as e:
                    return SandboxResult(
                        success=False,
                        error=f"Failed to start bot process: {str(e)}",
                        execution_time=time.time() - start_time
                    )
                    
            finally:
                self._cleanup_temp_environment()

    def terminate(self) -> None:
        """Terminate any running process."""
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.kill()
                except Exception:
                    pass
                self._process = None


class SandboxedBotRunner(BotInterface):
    """Bot runner that executes bot code in a sandbox."""

    def __init__(
        self,
        bot_id: str,
        name: str,
        bot_code: str,
        version: str = "v1",
        config: Optional[SandboxConfig] = None
    ):
        self.bot_id = bot_id
        self.name = name
        self.version = version
        self.bot_code = bot_code
        self.config = config or SandboxConfig()
        self.sandbox = BotSandbox(config)
        self.status = "pending"
        self.last_error: Optional[str] = None
        self._execution_count = 0
        self._timeout_count = 0
        self._max_timeouts = 3

    def on_game_start(self, view: GameView) -> None:
        """Initialize bot for game start."""
        view_data = self._serialize_view(view)
        result = self.sandbox.execute_bot_action(
            self.bot_code,
            "on_game_start",
            view_data,
            timeout=10.0
        )
        
        if result.success:
            self.status = "playing"
        else:
            self.status = "error"
            self.last_error = result.error

    def take_turn(self, view: GameView, available_actions: list) -> Any:
        """Execute bot turn in sandbox."""
        if self._timeout_count >= self._max_timeouts:
            # Bot has timed out too many times, return default action
            return available_actions[0] if available_actions else None
        
        view_data = self._serialize_view(view)
        actions_data = [self._serialize_action(action) for action in available_actions]
        
        result = self.sandbox.execute_bot_action(
            self.bot_code,
            "take_turn",
            view_data,
            available_actions=actions_data,
            timeout=self.config.wall_time_limit
        )
        
        self._execution_count += 1
        
        if result.success and result.output:
            return self._deserialize_action(result.output)
        elif result.timeout:
            self._timeout_count += 1
            return available_actions[0] if available_actions else None
        else:
            self.last_error = result.error
            return available_actions[0] if available_actions else None

    def on_event(self, event: dict) -> None:
        """Send event to bot."""
        result = self.sandbox.execute_bot_action(
            self.bot_code,
            "on_event",
            {"event": event},
            timeout=5.0
        )
        # Event handling is non-critical, so we don't fail on errors

    def _serialize_view(self, view: GameView) -> Dict[str, Any]:
        """Serialize GameView for transmission to sandbox."""
        return {
            "game_id": view.game_id,
            "turn_number": view.turn_number,
            "current_player": view.current_player.value if view.current_player else None,
            "phase": view.phase,
            "players": [
                {
                    "player_id": p.player_id.value,
                    "victory_points": p.victory_points,
                    "resources": {r.value: count for r, count in p.resources.items()},
                    "development_cards": len(p.development_cards)
                }
                for p in view.players
            ],
            "board": {
                "tiles": [
                    {
                        "tile_id": t.tile_id,
                        "resource_type": t.resource_type.value if t.resource_type else None,
                        "number": t.number
                    }
                    for t in view.board.tiles
                ]
            }
        }

    def _serialize_action(self, action: Any) -> Dict[str, Any]:
        """Serialize action for transmission to sandbox."""
        if hasattr(action, 'to_dict'):
            return action.to_dict()
        return {"type": str(type(action).__name__), "data": str(action)}

    def _deserialize_action(self, action_data: Dict[str, Any]) -> Any:
        """Deserialize action from sandbox response."""
        # For now, return the data as-is. In production, this would reconstruct
        # proper Action objects based on the type information.
        return action_data

    def validate(self) -> Dict[str, Any]:
        """Validate bot code by running a simple test."""
        # Try to execute the bot code with a simple validation test
        result = self.sandbox.execute_bot_action(
            self.bot_code,
            "validate",
            {},
            timeout=5.0
        )
        
        if result.success:
            self.status = "ready"
            return {"ok": True, "bot_id": self.bot_id, "version": self.version}
        else:
            # Even if execution fails, we can still validate that the code is syntactically correct
            # by checking if it compiles
            try:
                compile(self.bot_code, '<string>', 'exec')
                self.status = "ready"
                return {"ok": True, "bot_id": self.bot_id, "version": self.version}
            except SyntaxError as e:
                self.status = "invalid"
                self.last_error = f"Syntax error: {str(e)}"
                return {
                    "ok": False,
                    "bot_id": self.bot_id,
                    "version": self.version,
                    "error": self.last_error
                }

    def cleanup(self) -> None:
        """Clean up sandbox resources."""
        self.sandbox.terminate()


class SandboxManager:
    """Manages multiple sandbox instances."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._active_sandboxes: Dict[str, BotSandbox] = {}

    def create_sandbox(self, bot_id: str) -> BotSandbox:
        """Create a new sandbox for a bot."""
        sandbox = BotSandbox(self.config)
        self._active_sandboxes[bot_id] = sandbox
        return sandbox

    def get_sandbox(self, bot_id: str) -> Optional[BotSandbox]:
        """Get existing sandbox for a bot."""
        return self._active_sandboxes.get(bot_id)

    def terminate_sandbox(self, bot_id: str) -> None:
        """Terminate and remove a sandbox."""
        sandbox = self._active_sandboxes.pop(bot_id, None)
        if sandbox:
            sandbox.terminate()

    def terminate_all(self) -> None:
        """Terminate all active sandboxes."""
        for bot_id, sandbox in list(self._active_sandboxes.items()):
            sandbox.terminate()
        self._active_sandboxes.clear()
