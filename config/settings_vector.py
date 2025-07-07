from pydantic import BaseSettings
from typing import Optional


class VectorSettings(BaseSettings):
    vector_db_url: str
    vector_dim: int = 768
    index_type: str = "IVF_FLAT"

    class Config:
        env_file = ".env"
        env_prefix = "VECTOR_"
