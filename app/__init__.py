"""
RapidResolve Application Package

Core application configuration and initialization.
"""

from app.config import settings
from app.database import get_db, init_db, check_db_connection

__all__ = [
    "settings",
    "get_db",
    "init_db",
    "check_db_connection"
]