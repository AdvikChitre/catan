"""Simple in-memory bot package registry for the platform MVP."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BotPackage:
    bot_id: str
    name: str
    version: str
    entrypoint: str = "main.py"
    description: str = ""
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        self.validation_errors = []
        if not self.name or not self.name.strip():
            self.validation_errors.append("Bot name is required")
        if not self.version or not self.version.strip():
            self.validation_errors.append("Bot version is required")
        if not self.entrypoint or not self.entrypoint.strip():
            self.validation_errors.append("Entrypoint is required")
        self.validated = not self.validation_errors


class BotRegistry:
    """Tracks bot packages and immutable versions for the platform."""

    def __init__(self):
        self.packages: Dict[str, BotPackage] = {}
        self.versions: Dict[str, List[BotPackage]] = {}

    def register(self, name: str, version: str, entrypoint: str = "main.py", description: str = "") -> BotPackage:
        bot_id = f"{name}-{version}"
        package = BotPackage(
            bot_id=bot_id,
            name=name,
            version=version,
            entrypoint=entrypoint,
            description=description,
        )
        package.validate()
        self.packages[bot_id] = package
        self.versions.setdefault(name, [])
        self.versions[name].append(package)
        return package

    def list_bots(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for package in sorted(self.packages.values(), key=lambda pkg: (pkg.name, pkg.version)):
            items.append({
                "bot_id": package.bot_id,
                "name": package.name,
                "version": package.version,
                "entrypoint": package.entrypoint,
                "description": package.description,
                "validated": package.validated,
                "validation_errors": package.validation_errors,
            })
        return items

    def get_bot(self, bot_id: str) -> Optional[BotPackage]:
        return self.packages.get(bot_id)

    def get_versions(self, name: str) -> List[BotPackage]:
        return self.versions.get(name, [])
