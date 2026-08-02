"""Shared paths for local, non-versioned runtime data."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "runtime" / "vehicle_listings.sqlite3"
