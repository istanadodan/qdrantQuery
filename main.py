from fastapi.responses import JSONResponse
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi import Request, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from api.v1.mw import CreateAppContext, LogRequestMiddleware, TimeoutMonitor
from api.v1 import api
from api.v1.deps import get_db
import datetime
from dotenv import load_dotenv
from settings import logger_setting
import logging
import os

# from service.llm_search import agent


def setup():
    load_dotenv()
    os.environ["NUMEXPR_MAX_THREADS"] = "8"

    # 로깅 설정
    logger_setting()


def create_app():
    # app설정
    app = FastAPI()

    # 헬스체킹
    @app.get("/")
    def health_check():
        return {"status": "OK"}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    db = next(get_db())
    app.add_middleware(TimeoutMonitor, db=db)
    app.add_middleware(CreateAppContext, db=db)

    # app.add_middleware(LogRequestMiddleware)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        log_format = (
            "[{user_id}] {method} {url} {status} {response_time}ms - {content_length}"
        )

        try:
            start_time = datetime.datetime.now()
            response = await call_next(request)
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            user_id = (
                "unsigned_user"
                if "user_id" not in request.headers
                else request.headers["user_id"]
            )
            data = {
                "user_id": user_id,
                "method": request.method,
                "url": request.url.path,
                "status": response.status_code,
                "content_length": response.headers.get("content-length", "0"),
                "response_time": f"{duration * 1000:.2f}",
            }

            log_message = log_format.format(**data)
            logging.info(log_message)

            return response

        except Exception as e:
            _headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS, DELETE",
                "Access-Control-Allow-Headers": "*",
            }
            _err_content = str(e)
            _status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if not _err_content and hasattr(e, "detail"):
                _err_content = str(e.detail)
                _status_code = e.status_code

            return JSONResponse(
                content={"detail": _err_content},
                status_code=_status_code,
                headers=_headers,
            )

    app.include_router(api.api_router, prefix="/api/v1")
    app.mount(
        "/logo",
        StaticFiles(directory="mnt/static/company/logo_img"),
        name="logo_img_root",
    )
    return app


if __name__ == "__main__":
    # 설정값 로딩
    setup()

    app = create_app()

    uvicorn.run(app, host="0.0.0.0", port=8000)
