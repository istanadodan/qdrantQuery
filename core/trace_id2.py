# ============================================
# 파일: trace_context.py
# ============================================
"""
Trace ID를 관리하는 중앙 모듈
모든 다른 모듈에서 이 모듈을 import해서 사용
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# 전역 ContextVar 정의
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    """현재 trace ID를 반환"""
    return trace_id_var.get("")


def set_trace_id(trace_id: str) -> None:
    """trace ID를 설정"""
    trace_id_var.set(trace_id)


def generate_trace_id() -> str:
    """새로운 trace ID를 생성"""
    return str(uuid.uuid4())


def get_or_create_trace_id() -> str:
    """기존 trace ID가 있으면 반환, 없으면 새로 생성"""
    current_id = get_trace_id()
    if not current_id:
        current_id = generate_trace_id()
        set_trace_id(current_id)
    return current_id


# ============================================
# 파일: logging_utils.py
# ============================================
"""
로깅 유틸리티 모듈
trace_context에서 trace_id_var를 import해서 사용
"""

import logging
from typing import Any
from trace_context import trace_id_var, get_trace_id


class TraceLogger:
    """trace ID를 자동으로 포함하는 로깅 래퍼"""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log_with_trace(self, level: str, message: str, *args, **kwargs):
        trace_id = get_trace_id()
        if trace_id:
            prefixed_message = f"[trace_id:{trace_id}] {message}"
        else:
            prefixed_message = message

        getattr(self._logger, level)(prefixed_message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self._log_with_trace("info", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._log_with_trace("warning", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._log_with_trace("error", message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        self._log_with_trace("debug", message, *args, **kwargs)


class TraceLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter를 사용한 방법"""

    def process(self, msg: Any, kwargs: dict) -> tuple:
        trace_id = get_trace_id()
        if trace_id:
            msg = f"[trace_id:{trace_id}] {msg}"
        return msg, kwargs


def get_trace_logger(name: str) -> TraceLogger:
    """TraceLogger 인스턴스를 생성하는 팩토리 함수"""
    return TraceLogger(logging.getLogger(name))


# 전역 로깅 함수들
def log_info(message: str, *args, **kwargs):
    trace_id = get_trace_id()
    if trace_id:
        message = f"[trace_id:{trace_id}] {message}"
    logging.info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs):
    trace_id = get_trace_id()
    if trace_id:
        message = f"[trace_id:{trace_id}] {message}"
    logging.warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs):
    trace_id = get_trace_id()
    if trace_id:
        message = f"[trace_id:{trace_id}] {message}"
    logging.error(message, *args, **kwargs)


# ============================================
# 파일: middleware.py
# ============================================
"""
Starlette 미들웨어
trace_context에서 함수들을 import해서 사용
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from trace_context import get_trace_id, set_trace_id, generate_trace_id


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Trace ID를 생성하고 설정하는 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # 헤더에서 trace ID를 가져오거나 새로 생성
        trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()

        # ContextVar에 trace ID 설정
        set_trace_id(trace_id)

        # request.state에도 설정 (선택사항)
        request.state.trace_id = trace_id

        # 요청 처리
        response = await call_next(request)

        # 응답 헤더에 trace ID 추가
        response.headers["X-Trace-ID"] = trace_id

        return response


# ============================================
# 파일: services/user_service.py
# ============================================
"""
사용자 서비스 모듈
trace_context와 logging_utils에서 import
"""

from trace_context import get_trace_id
from logging_utils import get_trace_logger


class UserService:
    def __init__(self):
        # 모듈별 로거 생성
        self.logger = get_trace_logger(f"{__name__}.{self.__class__.__name__}")

    async def get_user(self, user_id: str):
        self.logger.info(f"Fetching user: {user_id}")

        # 직접 trace ID 접근도 가능
        current_trace_id = get_trace_id()
        self.logger.debug(f"Current trace ID: {current_trace_id}")

        # 사용자 조회 로직...
        if user_id == "invalid":
            self.logger.error(f"User not found: {user_id}")
            raise ValueError("User not found")

        self.logger.info(f"Successfully fetched user: {user_id}")
        return {"id": user_id, "name": "John Doe"}

    async def create_user(self, user_data: dict):
        self.logger.info("Creating new user")

        # 복잡한 사용자 생성 로직...
        await self._validate_user_data(user_data)
        user_id = await self._save_user(user_data)

        self.logger.info(f"User created successfully: {user_id}")
        return user_id

    async def _validate_user_data(self, user_data: dict):
        self.logger.debug("Validating user data")
        # 검증 로직...

    async def _save_user(self, user_data: dict):
        self.logger.debug("Saving user to database")
        # 저장 로직...
        return "user_123"


# ============================================
# 파일: services/order_service.py
# ============================================
"""
주문 서비스 모듈
다른 서비스와 동일하게 trace_context를 사용
"""

from trace_context import get_trace_id
from logging_utils import get_trace_logger, log_info


class OrderService:
    def __init__(self):
        self.logger = get_trace_logger(f"{__name__}.{self.__class__.__name__}")

    async def create_order(self, order_data: dict):
        self.logger.info("Starting order creation")

        # 전역 로깅 함수도 사용 가능
        log_info("Using global logging function")

        try:
            await self._validate_order(order_data)
            await self._process_payment(order_data)
            order_id = await self._save_order(order_data)

            self.logger.info(f"Order created successfully: {order_id}")
            return order_id

        except Exception as e:
            self.logger.error(f"Order creation failed: {str(e)}")
            raise

    async def _validate_order(self, order_data: dict):
        self.logger.debug("Validating order")
        # 검증 로직...

    async def _process_payment(self, order_data: dict):
        self.logger.debug("Processing payment")
        # 결제 처리 로직...

    async def _save_order(self, order_data: dict):
        self.logger.debug("Saving order")
        # 저장 로직...
        return "order_123"


# ============================================
# 파일: utils/database.py
# ============================================
"""
데이터베이스 유틸리티 모듈
trace_context를 사용해서 DB 쿼리에도 trace ID 포함
"""

from trace_context import get_trace_id
from logging_utils import get_trace_logger


class DatabaseConnection:
    def __init__(self):
        self.logger = get_trace_logger(f"{__name__}.{self.__class__.__name__}")

    async def execute_query(self, query: str, params: dict = None):
        trace_id = get_trace_id()

        self.logger.debug(f"Executing query: {query}")
        self.logger.debug(f"Query params: {params}")

        # 실제 DB 쿼리 실행...
        self.logger.info("Query executed successfully")

        return {"result": "success", "trace_id": trace_id}


# ============================================
# 파일: main.py
# ============================================
"""
메인 애플리케이션 파일
모든 모듈을 조합해서 사용
"""

import logging
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

# 우리가 만든 모듈들 import
from middleware import TraceIDMiddleware
from services.user_service import UserService
from services.order_service import OrderService
from utils.database import DatabaseConnection
from trace_context import get_trace_id
from logging_utils import get_trace_logger

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 서비스 인스턴스 생성
user_service = UserService()
order_service = OrderService()
db = DatabaseConnection()

# 메인 애플리케이션 로거
app_logger = get_trace_logger(__name__)


# 라우트 핸들러들
async def get_user(request: Request):
    user_id = request.path_params.get("user_id")
    app_logger.info(f"User request received: {user_id}")

    try:
        user = await user_service.get_user(user_id)
        return JSONResponse(user)
    except ValueError as e:
        app_logger.error(f"User request failed: {str(e)}")
        return JSONResponse(
            {"error": str(e), "trace_id": get_trace_id()}, status_code=404
        )


async def create_order(request: Request):
    order_data = await request.json()
    app_logger.info("Order creation request received")

    try:
        order_id = await order_service.create_order(order_data)
        return JSONResponse({"order_id": order_id, "trace_id": get_trace_id()})
    except Exception as e:
        app_logger.error(f"Order creation failed: {str(e)}")
        return JSONResponse(
            {"error": str(e), "trace_id": get_trace_id()}, status_code=500
        )


async def health_check(request: Request):
    app_logger.info("Health check requested")
    return JSONResponse({"status": "healthy", "trace_id": get_trace_id()})


# 라우트 설정
routes = [
    Route("/users/{user_id}", get_user),
    Route("/orders", create_order, methods=["POST"]),
    Route("/health", health_check),
]

# 앱 생성 및 미들웨어 추가
app = Starlette(debug=True, routes=routes)
app.add_middleware(TraceIDMiddleware)


# 예시: 모든 모듈에서 trace ID 접근 가능
def demonstrate_trace_sharing():
    """모든 모듈에서 trace ID에 접근할 수 있음을 보여주는 예시"""

    from trace_context import set_trace_id, get_trace_id

    # trace ID 설정
    set_trace_id("demo-trace-123")

    # 모든 모듈에서 동일한 trace ID 사용
    user_service.logger.info("User service log")
    order_service.logger.info("Order service log")
    db.logger.info("Database log")
    app_logger.info("App log")

    # 모든 로그에 동일한 trace ID가 포함됨
    print(f"Current trace ID: {get_trace_id()}")


if __name__ == "__main__":
    demonstrate_trace_sharing()

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
