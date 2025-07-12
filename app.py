from fastapi.responses import JSONResponse, Response
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi import Request, FastAPI, status


# from api.v1.mw import CreateAppContext, LogRequestMiddleware, TimeoutMonitor
from api.v1 import api_route
from dotenv import load_dotenv
from core.loggings import setup_logging, logging
from core.middlewares import logging_handler, cors_handler
import os

load_dotenv()

# 로깅 설정
setup_logging()


# from service.llm_search import agent
logger = logging.getLogger(__name__)


def create_app():
    # app설정
    app = FastAPI()

    # 헬스체킹
    @app.get("/")
    def health_check():
        return Response(content="OK")

    app.include_router(api_route.api_router, prefix="/api/v1")
    # app.mount(
    #     "/logo",
    #     StaticFiles(directory="mnt/static/company/logo_img"),
    #     name="logo_img_root",
    # )

    # 서비스로깅 자동처리 등록
    logging_handler(app)

    # web 설정
    cors_handler(app)
    # db = next(get_db())
    # app.add_middleware(TimeoutMonitor, db=db)
    # app.add_middleware(CreateAppContext, db=db)

    # app.add_middleware(LogRequestMiddleware)
    return app


if __name__ == "__main__":
    # 설정값 로딩
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
