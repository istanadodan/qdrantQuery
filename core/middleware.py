import datetime
from fastapi import FastAPI
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging


logger = logging.getLogger(__name__)


def add_middleware(app: FastAPI):
    app.add_middleware(LoggingMiddleware)
    cors_handler(app)


def cors_handler(app: FastAPI):
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger_=None):
        super().__init__(app)
        self.logger = logger_ or logger

    async def dispatch(self, request: Request, call_next):
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

            logger.info(log_format.format(**data))

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


from starlette.types import ASGIApp, Message, Receive, Scope, Send
import asyncio
import time
import traceback


class TimeoutMonitor:
    REQUEST_TIMEOUT_SECOD = 10 * 60  # 타임아웃(초)

    def __init__(self, app, db):
        self.app = app
        self.db = db

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            start_time = time.time()
            response = await asyncio.wait_for(
                self.app(scope, receive, send), timeout=self.REQUEST_TIMEOUT_SECOD
            )
            return response
        except asyncio.TimeoutError:
            process_time = time.time() - start_time
            logger.error(
                f"[처리시간:{process_time}s] 타임아웃 발생되어 처리가 종료됩니다"
            )
            traceback.print_exc()
            self.db.rollback()
            return TimeoutError(process_time=process_time)
