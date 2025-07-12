import uvicorn
from dotenv import load_dotenv
from core.logging import setup_logging, logging

load_dotenv()

# 로깅 설정
setup_logging()

logger = logging.getLogger(__name__)


def create_app():
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    from core.middleware import logging_handler, cors_handler
    from api.v1 import api_route

    # app설정
    app = FastAPI(title="test api")

    # 헬스체킹
    @app.get("/")
    def health_check():
        return JSONResponse(content={"status": "OK"})

    app.include_router(api_route.router, prefix="/api/v1")
    app.mount(
        "/static",
        StaticFiles(directory="mnt/static/"),
        name="static",
    )

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
    uvicorn.run(app, host="localhost", port=8000)
