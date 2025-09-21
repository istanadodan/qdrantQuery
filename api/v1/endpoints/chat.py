from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_db
from core.database import async_sessionmaker
from sqlalchemy import select, and_
from models import User
from schemas.user_schema import User as UserSchema
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/", response_model=UserSchema)
async def chat(db: async_sessionmaker = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_id == 1))
    user = result.scalar_one_or_none()

    user_schema = UserSchema.model_validate(user)

    # return JSONResponse(user_schema.model_dump_json())
    return user_schema
