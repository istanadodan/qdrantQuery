from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_db

router = APIRouter()


@router.get("/")
async def index(db: AsyncSession = Depends(get_db)):
    return Response(str(await db.scalar("test")))
