from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from src.utils.config import Settings

def get_engine(settings: Settings) -> Engine:
    # pool_pre_ping avoids stale connections
    return create_engine(settings.pg_url, pool_pre_ping=True)