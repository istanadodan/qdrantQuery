from fastapi import APIRouter, Response, Depends
from api.dependencies import get_db

router = APIRouter()


@router.get("/")
def index(db=Depends(get_db)):
    return Response("OK")
