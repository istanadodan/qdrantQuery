from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Generator, AsyncGenerator
from .database import get_db_session
from .vector_db import get_vector_client


def get_db(
    session: Session = Depends(get_db_session),
) -> Generator[Session, None, None]:
    try:
        yield session
    finally:
        session.close()


async def get_vector_db():
    client = await get_vector_client()
    try:
        yield client
    finally:
        await client.close()
