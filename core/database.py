from core.settings import db_setting
import json
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
import logging

logger = logging.getLogger(__name__)

DB_URL = (
    f"mysql+asyncmy://"
    f"{db_setting.username1}:"
    f"{db_setting.password}@"
    f"{db_setting.db_host}:"
    f"{db_setting.db_port}/"
    f"{db_setting.db_name}"
)

async_engine: AsyncEngine = create_async_engine(
    url=DB_URL,
    future=True,
    pool_size=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    json_serializer=lambda x: json.dumps(x, ensure_ascii=False, indent=2),
    echo=True,
)
async_session: async_sessionmaker = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    future=True,
)


async def check_db_connection():

    from sqlalchemy import text, select
    from models.user import User

    logger.info(f"spool size: {async_engine.pool.size()}")

    try:
        async with async_engine.connect() as conn:

            await conn.execute(text("SELECT 1"))
            user = await conn.execute(select(User))
            logger.info(user.fetchone().username)
            logger.info("DB 연결 성공!")
    except Exception as e:
        print("DB 연결 실패:", e)
    finally:
        await async_engine.dispose()


# 동기형
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# engine = create_engine(db_setting.database_url)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()
# Base.metadata.create_all(bind=engine)


class AsyncSessionContext:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session: async_sessionmaker = async_session()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        self.session = None


from functools import wraps


def async_transactional(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if "session" in kwargs:
            return await func(*args, **kwargs)

        else:
            async with AsyncSessionContext() as session:
                kwargs["session"] = session

            try:
                result = await func(*args, **kwargs)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise e

            return result

    return wrapper
