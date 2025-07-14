from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_db
from core.database import async_sessionmaker
from sqlalchemy import select, and_
from models import User

router = APIRouter()


@router.get("/")
async def index(db: async_sessionmaker = Depends(get_db)):
    result = await db.execute(select(User))
    user = result.scalar_one_or_none()
    return JSONResponse(user)
