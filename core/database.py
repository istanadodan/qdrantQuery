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
"""
설정 옵션 설명:
pool_size: 풀에 유지할 최대 연결 수입니다. 
max_overflow: pool_size를 초과하여 생성할 수 있는 최대 연결 수입니다. 
pool_recycle: 초 단위로 연결이 재활용되기 전에 유지되는 시간입니다. MySQL 서버의 wait_timeout 설정보다 짧게 설정하는 것이 좋습니다. 
pool_pre_ping: 연결이 유효한지 확인하기 위해 풀에서 연결을 가져올 때마다 검사합니다. MySQL 8.0 이상에서 권장됩니다. 
poolclass: 사용할 풀 클래스를 지정합니다. NullPool을 사용하면 연결 풀링을 사용하지 않습니다. 
연결 풀 작동 확인:
위 코드 예시에서 볼 수 있듯이, `engine.connect()`를 사용하여 연결을 가져오고, `conn.execute(text("SELECT 1"))`과 같이 간단한 쿼리를 실행하여 연결이 정상적으로 작동하는지 확인할 수 있습니다. 
참고:
MySQL 서버의 wait_timeout 설정은 MySQL 서버의 설정 파일 (예: my.cnf) 에서 확인하거나, MySQL 클라이언트를 통해 SHOW VARIABLES LIKE 'wait_timeout'; 명령어를 실행하여 확인할 수 있습니다.
pool_recycle 설정은 MySQL 서버의 wait_timeout 설정보다 짧게 설정하여, 연결이 끊어지기 전에 재활용되도록 하는 것이 좋습니다.
pool_pre_ping 옵션은 MySQL 8.0 이상에서 연결 검사를 위해 권장됩니다. 
autoClosingQuates
"""
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


def test2():
    from fastembed import SparseTextEmbedding


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
