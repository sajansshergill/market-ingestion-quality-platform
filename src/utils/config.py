from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    pg_host: str = os.getenv("PG_HOST") or os.getenv("PGHOST", "localhost")
    pg_port: int = int(os.getenv("PG_PORT") or os.getenv("PGPORT", "5432"))
    pg_db: str = os.getenv("PG_DB", "warehouse")
    pg_user: str = os.getenv("PG_USER") or os.getenv("PGUSER", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "postgres")
    
    fred_api_key: str | None = os.getenv("FRED_API_KEY")
    
    @property
    def pg_url(self) -> str:
        return f"postgresql+psycopg2://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_db}"