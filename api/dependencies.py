from fastapi import HTTPException, Depends, status, Request
from fastapi.security import APIKeyHeader
from core.database import async_session
from sqlalchemy.exc import SQLAlchemyError

api_key_header = APIKeyHeader(name="id", auto_error=False)


def decode_auth_header(id: str = Depends(api_key_header)):
    if id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Please Logout and Login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return id


async def get_db():
    db = async_session()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLAlchemyError(e)
    finally:
        db.close()
