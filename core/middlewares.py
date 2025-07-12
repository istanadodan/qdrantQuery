from fastapi import FastAPI
import logging
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
import datetime


def logging_handler(app: FastAPI):
    app.add_middleware(LoggingMiddleware)


def cors_handler(app: FastAPI):
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger=None):
        super().__init__(app)
        self.logger = logger or logging.getLogger(__name__)

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
