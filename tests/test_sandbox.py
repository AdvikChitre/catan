"""Tests for bot sandbox execution environment."""

import json
import pytest
from src.platform.sandbox import (
    BotSandbox,
    SandboxConfig,
    SandboxResult,
    SandboxedBotRunner,
    SandboxManager
)


class TestBotSandbox:
    """Test basic sandbox execution."""

    def test_create_sandbox(self):
        """Test sandbox creation."""
        config = SandboxConfig()
        sandbox = BotSandbox(config)
        assert sandbox.config == config
        assert sandbox._temp_dir is None
        assert sandbox._process is None

    def test_simple_bot_execution(self):
        """Test executing a simple bot action."""
        sandbox = BotSandbox()
        bot_code = """
import json
import sys

if __name__ == "__main__":
    input_file = sys.argv[1]
    with open(input_file, 'r') as f:
        input_data = json.load(f)
    
    result = {"action": "test_action", "value": 42}
    print(json.dumps(result))
"""
        result = sandbox.execute_bot_action(
            bot_code,
            "test",
            {"test": "data"},
            timeout=10.0
        )
        
        assert result.success is True
        assert result.output is not None
        assert result.output["value"] == 42
        assert result.timeout is False

    def test_bot_timeout(self):
        """Test bot execution timeout."""
        sandbox = BotSandbox(SandboxConfig(wall_time_limit=1.0))
        bot_code = """
import time
time.sleep(10)
print("should not reach here")
"""
        result = sandbox.execute_bot_action(
            bot_code,
            "test",
            {},
            timeout=1.0
        )
        
        assert result.success is False
        assert result.timeout is True
        assert "timeout" in result.error.lower()

    def test_bot_syntax_error(self):
        """Test bot with syntax error."""
        sandbox = BotSandbox()
        bot_code = """
def broken_function(
    # Missing closing parenthesis
    print("syntax error")
"""
        result = sandbox.execute_bot_action(
            bot_code,
            "test",
            {},
            timeout=5.0
        )
        
        assert result.success is False
        assert result.error is not None
        assert result.exit_code != 0

    def test_temp_cleanup(self):
        """Test temporary directory cleanup."""
        sandbox = BotSandbox()
        bot_code = """
import json
import sys
if __name__ == "__main__":
    print(json.dumps({"result": "ok"}))
"""
        result = sandbox.execute_bot_action(
            bot_code,
            "test",
            {},
            timeout=5.0
        )
        
        assert result.success is True
        assert sandbox._temp_dir is None  # Should be cleaned up


class TestSandboxedBotRunner:
    """Test sandboxed bot runner integration."""

    def test_runner_creation(self):
        """Test creating a sandboxed bot runner."""
        bot_code = """
def on_game_start(view):
    return {"status": "ready"}

def take_turn(view, available_actions):
    return available_actions[0] if available_actions else None
"""
        runner = SandboxedBotRunner(
            bot_id="test-bot",
            name="Test Bot",
            bot_code=bot_code,
            version="v1"
        )
        
        assert runner.bot_id == "test-bot"
        assert runner.name == "Test Bot"
        assert runner.version == "v1"
        assert runner.status == "pending"

    def test_runner_validation(self):
        """Test bot validation."""
        bot_code = """
import json
import sys

def on_game_start(view):
    return {"status": "ready"}

def take_turn(view, available_actions):
    return available_actions[0] if available_actions else None

if __name__ == "__main__":
    # Validation test - just output success
    print(json.dumps({"status": "VALID"}))
"""
        runner = SandboxedBotRunner(
            bot_id="test-bot",
            name="Test Bot",
            bot_code=bot_code,
            version="v1"
        )
        
        result = runner.validate()
        assert result["ok"] is True
        assert runner.status == "ready"

    def test_runner_timeout_tracking(self):
        """Test that runner tracks timeouts and falls back to default action."""
        bot_code = """
import json
import sys
import time

def take_turn(view, available_actions):
    time.sleep(100)  # Simulate slow bot
    return available_actions[0]

if __name__ == "__main__":
    input_file = sys.argv[1]
    with open(input_file, 'r') as f:
        input_data = json.load(f)
    
    # Simulate timeout behavior on take_turn
    if input_data.get("action") == "take_turn":
        time.sleep(100)  # This will timeout
        print(json.dumps({"action": "build_road"}))
    else:
        print(json.dumps({"status": "ok"}))
"""
        config = SandboxConfig(wall_time_limit=0.5)
        runner = SandboxedBotRunner(
            bot_id="slow-bot",
            name="Slow Bot",
            bot_code=bot_code,
            version="v1",
            config=config
        )
        
        # Mock view and actions for testing
        class MockView:
            game_id = "test-game"
            turn_number = 1
            current_player = None
            phase = "playing"
            players = []
            board = type('obj', (object,), {'tiles': []})()
        
        mock_view = MockView()
        mock_actions = [{"type": "build_road"}]
        
        # First timeout - should increment timeout count and return default action
        result = runner.take_turn(mock_view, mock_actions)
        # Should return the default action due to timeout
        assert result is not None
        assert runner._timeout_count >= 1
        
        # Second timeout
        result = runner.take_turn(mock_view, mock_actions)
        assert result is not None
        assert runner._timeout_count >= 2

    def test_runner_cleanup(self):
        """Test runner cleanup."""
        bot_code = "def on_game_start(view): pass"
        runner = SandboxedBotRunner(
            bot_id="test-bot",
            name="Test Bot",
            bot_code=bot_code,
            version="v1"
        )
        
        runner.cleanup()
        # Should not raise any exceptions


class TestSandboxManager:
    """Test sandbox manager for multiple sandboxes."""

    def test_manager_creation(self):
        """Test creating a sandbox manager."""
        manager = SandboxManager()
        assert len(manager._active_sandboxes) == 0

    def test_create_and_get_sandbox(self):
        """Test creating and retrieving sandboxes."""
        manager = SandboxManager()
        sandbox1 = manager.create_sandbox("bot-1")
        sandbox2 = manager.create_sandbox("bot-2")
        
        assert sandbox1 is not None
        assert sandbox2 is not None
        assert sandbox1 is not sandbox2
        
        retrieved = manager.get_sandbox("bot-1")
        assert retrieved is sandbox1

    def test_terminate_sandbox(self):
        """Test terminating individual sandbox."""
        manager = SandboxManager()
        sandbox = manager.create_sandbox("bot-1")
        
        manager.terminate_sandbox("bot-1")
        
        assert manager.get_sandbox("bot-1") is None

    def test_terminate_all(self):
        """Test terminating all sandboxes."""
        manager = SandboxManager()
        manager.create_sandbox("bot-1")
        manager.create_sandbox("bot-2")
        manager.create_sandbox("bot-3")
        
        manager.terminate_all()
        
        assert len(manager._active_sandboxes) == 0


class TestSandboxConfig:
    """Test sandbox configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SandboxConfig()
        assert config.cpu_time_limit == 30.0
        assert config.wall_time_limit == 60.0
        assert config.memory_limit_mb == 256
        assert config.max_processes == 10
        assert config.network_disabled is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SandboxConfig(
            cpu_time_limit=10.0,
            wall_time_limit=20.0,
            memory_limit_mb=128,
            network_disabled=False
        )
        assert config.cpu_time_limit == 10.0
        assert config.wall_time_limit == 20.0
        assert config.memory_limit_mb == 128
        assert config.network_disabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
