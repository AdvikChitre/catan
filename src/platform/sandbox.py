"""Legacy settings retained for stored versions; not a security boundary.

Execution is implemented by src.player.process.ProcessPlayer. OS isolation for
public untrusted hosting is deployment-specific; this application is local.
"""
from dataclasses import dataclass

@dataclass
class SandboxConfig:
    cpu_time_limit: float = 30
    wall_time_limit: float = 2
    memory_limit_mb: int = 256
    max_processes: int = 10
    max_threads: int = 20
    temp_fs_limit_mb: int = 100
    network_disabled: bool = True
