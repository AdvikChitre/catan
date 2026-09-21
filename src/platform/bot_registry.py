"""Bot package registry for the platform with database persistence."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .sandbox import SandboxConfig
from .database import DatabaseManager, BotRepository, Bot as DBBot


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
    bot_code: Optional[str] = None
    use_sandbox: bool = False
    sandbox_config: Optional[SandboxConfig] = None

    def validate(self) -> None:
        self.validation_errors = []
        if not self.name or not self.name.strip():
            self.validation_errors.append("Bot name is required")
        if not self.version or not self.version.strip():
            self.validation_errors.append("Bot version is required")
        if not self.entrypoint or not self.entrypoint.strip():
            self.validation_errors.append("Entrypoint is required")
        if self.use_sandbox and not self.bot_code:
            self.validation_errors.append("Bot code is required for sandboxed execution")
        self.validated = not self.validation_errors


class BotRegistry:
    """Tracks bot packages and immutable versions for the platform with database persistence."""

    def __init__(self, use_database: bool = True, database_url: str = "sqlite:///catan_platform.db"):
        self.use_database = use_database
        if use_database:
            self.db_manager = DatabaseManager(database_url)
            self.db_manager.create_tables()
            self.bot_repository = BotRepository(self.db_manager)
        else:
            # Fallback to in-memory storage
            self.packages: Dict[str, BotPackage] = {}
            self.versions: Dict[str, List[BotPackage]] = {}

    def register(
        self,
        name: str,
        version: str,
        entrypoint: str = "main.py",
        description: str = "",
        bot_code: Optional[str] = None,
        use_sandbox: bool = False,
        sandbox_config: Optional[SandboxConfig] = None,
        owner_id: Optional[str] = None
    ) -> BotPackage:
        bot_id = f"{name}-{version}"
        
        if self.use_database:
            # Convert sandbox config to dict for database storage
            sandbox_config_dict = None
            if sandbox_config:
                sandbox_config_dict = {
                    "cpu_time_limit": sandbox_config.cpu_time_limit,
                    "wall_time_limit": sandbox_config.wall_time_limit,
                    "memory_limit_mb": sandbox_config.memory_limit_mb,
                    "max_processes": sandbox_config.max_processes,
                    "network_disabled": sandbox_config.network_disabled,
                }
            
            # Create bot in database
            db_bot = self.bot_repository.create_bot(
                bot_id=bot_id,
                name=name,
                version=version,
                entrypoint=entrypoint,
                description=description,
                bot_code=bot_code,
                use_sandbox=use_sandbox,
                sandbox_config=sandbox_config_dict,
                owner_id=owner_id
            )
            
            # Validate the bot package
            temp_package = BotPackage(
                bot_id=bot_id,
                name=name,
                version=version,
                entrypoint=entrypoint,
                description=description,
                bot_code=bot_code,
                use_sandbox=use_sandbox,
                sandbox_config=sandbox_config,
            )
            temp_package.validate()
            
            # Update validation status in database
            self.bot_repository.update_bot_validation(
                bot_id,
                temp_package.validated,
                temp_package.validation_errors
            )
            
            # Create BotPackage wrapper with validation results
            package = BotPackage(
                bot_id=db_bot.id,
                name=db_bot.name,
                version=db_bot.version,
                entrypoint=db_bot.entrypoint,
                description=db_bot.description,
                validated=temp_package.validated,
                validation_errors=temp_package.validation_errors,
                bot_code=db_bot.bot_code,
                use_sandbox=db_bot.use_sandbox,
                sandbox_config=sandbox_config,
            )
        else:
            # In-memory storage
            package = BotPackage(
                bot_id=bot_id,
                name=name,
                version=version,
                entrypoint=entrypoint,
                description=description,
                bot_code=bot_code,
                use_sandbox=use_sandbox,
                sandbox_config=sandbox_config,
            )
            package.validate()
            self.packages[bot_id] = package
            self.versions.setdefault(name, [])
            self.versions[name].append(package)
        
        return package

    def list_bots(self, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_database:
            db_bots = self.bot_repository.list_bots(owner_id=owner_id)
            return [bot.to_dict() for bot in db_bots]
        else:
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
                    "use_sandbox": package.use_sandbox,
                })
            return items

    def get_bot(self, bot_id: str) -> Optional[BotPackage]:
        if self.use_database:
            db_bot = self.bot_repository.get_bot(bot_id)
            if db_bot:
                validation_errors = json.loads(db_bot.validation_errors) if db_bot.validation_errors else []
                return BotPackage(
                    bot_id=db_bot.id,
                    name=db_bot.name,
                    version=db_bot.version,
                    entrypoint=db_bot.entrypoint,
                    description=db_bot.description,
                    validated=db_bot.validated,
                    validation_errors=validation_errors,
                    bot_code=db_bot.bot_code,
                    use_sandbox=db_bot.use_sandbox,
                )
            return None
        else:
            return self.packages.get(bot_id)

    def get_versions(self, name: str) -> List[BotPackage]:
        if self.use_database:
            db_bots = self.bot_repository.list_bots()
            return [self._db_bot_to_package(bot) for bot in db_bots if bot.name == name]
        else:
            return self.versions.get(name, [])
    
    def _db_bot_to_package(self, db_bot) -> BotPackage:
        """Convert database bot to BotPackage."""
        validation_errors = json.loads(db_bot.validation_errors) if db_bot.validation_errors else []
        return BotPackage(
            bot_id=db_bot.id,
            name=db_bot.name,
            version=db_bot.version,
            entrypoint=db_bot.entrypoint,
            description=db_bot.description,
            validated=db_bot.validated,
            validation_errors=validation_errors,
            bot_code=db_bot.bot_code,
            use_sandbox=db_bot.use_sandbox,
        )
    
    def update_validation(
        self,
        bot_id: str,
        validated: bool,
        validation_errors: Optional[List[str]] = None
    ) -> bool:
        """Update bot validation status."""
        if self.use_database:
            result = self.bot_repository.update_bot_validation(bot_id, validated, validation_errors)
            return result is not None
        else:
            package = self.packages.get(bot_id)
            if package:
                package.validated = validated
                package.validation_errors = validation_errors or []
                return True
            return False
