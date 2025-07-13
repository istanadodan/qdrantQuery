from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os

PROFILE = os.environ.get("PROFILE", "dev")


class Config_:
    env_file = str(Path(f"{PROFILE}.env").absolute())
    extra = "allow"


class DatabaseSettings(BaseSettings):
    username1: str
    password: str
    db_host: str
    db_port: str
    db_name: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    class Config(Config_):
        """env_prefix = "DB_"""


class VectorSettings(BaseSettings):
    vector_db_url: str
    vector_dim: int = 768
    index_type: str = "IVF_FLAT"

    class Config(Config_):
        """env_prefix = "DB_"""


db_setting = DatabaseSettings()
