from core.settings import db_setting
import json
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

DB_URL = (
    f"mysql+asyncmy://"
    f"{db_setting.username}:"
    f"{db_setting.password}@"
    f"{db_setting.db_host}:"
    f"{db_setting.db_port}/"
    f"{db_setting.db_name}"
)

async_engine: AsyncEngine = create_async_engine(
    url=DB_URL,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    json_serializer=lambda x: json.dumps(x, ensure_ascii=False, indent=2),
)
async_session: async_sessionmaker = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    future=True,
)

# 동기형
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# engine = create_engine(db_setting.database_url)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()
# Base.metadata.create_all(bind=engine)
