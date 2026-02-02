"""
Data module for Credit Spreading Tool.

This module handles data loading from JSON ticker files and SQLite database operations.
"""

from .data_loader import DataLoader
from .database import DatabaseManager

__all__ = ["DataLoader", "DatabaseManager"]
