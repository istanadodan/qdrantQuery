import datetime
import json
from fastapi import FastAPI
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import asyncio
import time
import traceback


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

        if request.method == "GET":
            params = request.query_params or request.path_params
        else:
            params = await self._getRequestBody(request)

        try:
            start_time = datetime.datetime.now()

            response = await call_next(request)

            duration = (datetime.datetime.now() - start_time).total_seconds()
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
                "request_params": params,
                "request_body": await self._getResponseBody(response),
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

    async def _getRequestBody(request: Request) -> str:
        """_본문은 streaming으로, 값 추출후 흐름 재설정해야 함

        :param request: Description
        :type request: Request
        :return: Description
        :rtype: str
        """
        body = await request.body()
        if not body:
            return ""

        decoded_body = body.decode("utf-8")
        try:
            json_body = json.loads(decoded_body)
            request.state.json_body = json_body
            return json.dumps(json_body, ensure_ascii=False)
        except:
            request.state.raw_body = decoded_body
            return decoded_body

    async def _getResponseBody(self, response: StreamingResponse) -> str:
        """
        본문은 streaming으로, 값 추출후 흐름 재설정해야 함

        :param response: Description
        :type response: Any
        :return: Description
        :rtype: str
        """
        body_content = b""
        collected_chunks = []
        async for chunk in response.body_iterator:
            collected_chunks.append(
                chunk if isinstance(chunk, bytes) else str(chunk).encode("utf-8")
            )

        response.body_iterator = self._recreate_body_iterator(collected_chunks)
        return self._concat_and_decode(collected_chunks)

    async def _recreate_body_iterator(self, chunks: list[bytes]) -> "Generator":
        """body iterator 재생성"""
        for chunk in chunks:
            yield chunk

    def _concat_and_decode(self, chunks: list[bytes]) -> str:
        content_bytes = "".join(chunks)
        try:
            return json.dumps(content_bytes.decode("utf-8"), ensure_ascii=False)
        except:
            return content_bytes.decode("utf-8", errors="ignore")


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
