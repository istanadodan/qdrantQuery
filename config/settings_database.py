from pydantic import BaseSettings
from typing import Optional


class DatabaseSettings(BaseSettings):
    database_url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    class Config:
        env_file = ".env"
        env_prefix = "DB_"
