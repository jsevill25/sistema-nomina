"""Compatibility exports for the core services."""

from .common import *  # noqa: F401,F403
from .theme import CorporateThemeManager
from .config import BCVClient, ConfigManager
from .database import DatabaseManager
from .events import EventBus
from .auth import AuthController
from .registry import ModuleBase, ModuleRegistry
