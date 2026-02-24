"""Tests for config module."""
from __future__ import annotations

import os

import pytest

from src.utils.config import Settings


def test_settings_defaults():
    """Settings loads with sensible defaults."""
    s = Settings()
    assert s.pg_host in ("localhost", "127.0.0.1") or s.pg_host
    assert s.pg_port > 0
    assert s.pg_db == "warehouse"
    assert s.pg_user == "postgres"


def test_pg_url():
    """pg_url builds valid connection string."""
    s = Settings()
    url = s.pg_url
    assert "postgresql" in url
    assert "warehouse" in url
