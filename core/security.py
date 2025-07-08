from datetime import datetime, timedelta
import logging
from typing import Union
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from dependencies import RedisConn, settings

JWT_SECRET = settings.JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 1
REDIS_HASH_NAME_FOR_TOKENS = "tokens"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Union[str, None] = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(user_id):
    token = jwt.encode(
        {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
        },
        JWT_SECRET,
        algorithm=ALGORITHM,
    )
    RedisConn.hset(REDIS_HASH_NAME_FOR_TOKENS, user_id, token)
    return token


def delete_access_token(user_id):
    RedisConn.hdel(REDIS_HASH_NAME_FOR_TOKENS, user_id)


def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please Logout and Login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        userid: str = payload.get("user_id")
        if userid is None:
            raise credentials_exception
        if token != RedisConn.hget(REDIS_HASH_NAME_FOR_TOKENS, userid):
            raise credentials_exception
    except JWTError:
        logging.error(f"[토큰 오류]\ntoken: {token}")
        raise credentials_exception
    return userid


# 사용자토큰을 취득한다.
def get_access_token(user_id) -> str:
    return RedisConn.hget(REDIS_HASH_NAME_FOR_TOKENS, user_id)
