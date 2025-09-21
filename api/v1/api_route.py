from fastapi import APIRouter
from api.v1.endpoints import user, chat

router = APIRouter()
router.include_router(user.router, prefix="/user", tags=["User"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
