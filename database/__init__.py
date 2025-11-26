"""Database package."""
from .mongo import MongoDB, get_db, db

__all__ = ["MongoDB", "get_db", "db"]