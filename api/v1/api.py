from fastapi import APIRouter
from api.v1.endpoints import ai, document, user, auth, common

api_router = APIRouter()
api_router.include_router(ai.router, prefix="/ai", tags=["LLM + Retrieval"])
api_router.include_router(document.router, prefix="/document", tags=["문서관리"])
api_router.include_router(user.router, prefix="/user", tags=["사용자관리"])
api_router.include_router(auth.router, prefix="/auth", tags=["인증 및 권한"])
api_router.include_router(common.router, prefix="/common", tags=["공통"])
