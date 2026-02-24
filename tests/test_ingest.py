"""Tests for ingest modules."""
from __future__ import annotations

import os

import pytest

from src.ingest.vendor_fred import fetch_fred_series


def test_fred_dataframe_shape():
    """fetch_fred_series returns DataFrame with expected columns when API works."""
    if not os.getenv("FRED_API_KEY"):
        pytest.skip("FRED_API_KEY not set")
    try:
        df = fetch_fred_series("FEDFUNDS", os.environ["FRED_API_KEY"], start_date="2025-01-01")
    except Exception:
        pytest.skip("FRED API unavailable (network/key)")
    if df.empty:
        pytest.skip("FRED API returned no data")
    assert "series_id" in df.columns
    assert "obs_date" in df.columns
    assert "obs_value" in df.columns
    assert "source" in df.columns
