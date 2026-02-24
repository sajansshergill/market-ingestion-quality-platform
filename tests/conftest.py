"""Pytest configuration and fixtures."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Ensure .env is loaded and test DB vars can override."""
    os.environ.setdefault("PGHOST", "localhost")
    os.environ.setdefault("PGPORT", "5440")
    yield
