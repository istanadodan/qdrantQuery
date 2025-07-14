import logging
import uuid
from contextvars import ContextVar
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

# Context variable to store trace ID
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and set trace ID for each request"""

    async def dispatch(self, request: Request, call_next):
        # Generate trace ID (or extract from headers if provided)
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())

        # Set trace ID in context variable
        trace_id_var.set(trace_id)

        # Add trace ID to request state for easy access
        request.state.trace_id = trace_id

        # Process request
        response = await call_next(request)

        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = trace_id

        return response


class TraceIDFormatter(logging.Formatter):
    """Custom formatter that includes trace ID in log messages"""

    def format(self, record):
        # Get trace ID from context variable
        trace_id = trace_id_var.get("")

        # Add trace ID to log record
        record.trace_id = trace_id

        return super().format(record)


# Configure logging with trace ID
def setup_logging():
    formatter = TraceIDFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [trace_id:%(trace_id)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


# Initialize logging
logger = setup_logging()


# Example route handlers
async def hello(request: Request):
    logger.info("Processing hello request")

    # You can also access trace ID directly from request state
    trace_id = request.state.trace_id
    logger.info(f"Handling request with trace ID: {trace_id}")

    return JSONResponse({"message": "Hello, World!", "trace_id": trace_id})


async def error_example(request: Request):
    logger.warning("This is a warning message")

    try:
        # Simulate an error
        raise ValueError("Something went wrong")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return JSONResponse(
            {"error": "Internal server error", "trace_id": request.state.trace_id},
            status_code=500,
        )


# Alternative: Using a logger wrapper for cleaner code
class TraceLogger:
    """Logger wrapper that automatically includes trace ID"""

    def __init__(self, logger):
        self.logger = logger

    def _log(self, level, message, *args, **kwargs):
        trace_id = trace_id_var.get("")
        prefixed_message = f"[trace_id:{trace_id}] {message}"
        getattr(self.logger, level)(prefixed_message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self._log("info", message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self._log("warning", message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self._log("error", message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        self._log("debug", message, *args, **kwargs)


# Usage with wrapper
trace_logger = TraceLogger(logging.getLogger(__name__))


async def wrapper_example(request: Request):
    trace_logger.info("Using trace logger wrapper")
    trace_logger.warning("This warning includes trace ID automatically")

    return JSONResponse({"message": "Using wrapper logger"})


# Routes
routes = [
    Route("/", hello),
    Route("/error", error_example),
    Route("/wrapper", wrapper_example),
]

# Create Starlette app
app = Starlette(debug=True, routes=routes)

# Add middleware
app.add_middleware(TraceIDMiddleware)


# Example of how to use in a more complex service
class UserService:
    def __init__(self):
        self.logger = TraceLogger(
            logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        )

    async def get_user(self, user_id: str):
        self.logger.info(f"Fetching user: {user_id}")

        # Simulate database call
        if user_id == "invalid":
            self.logger.error(f"User not found: {user_id}")
            raise ValueError("User not found")

        self.logger.info(f"Successfully fetched user: {user_id}")
        return {"id": user_id, "name": "John Doe"}


# Service usage example
user_service = UserService()


async def get_user_endpoint(request: Request):
    user_id = request.path_params.get("user_id")

    try:
        user = await user_service.get_user(user_id)
        return JSONResponse(user)
    except ValueError as e:
        return JSONResponse(
            {"error": str(e), "trace_id": request.state.trace_id}, status_code=404
        )


# Add user route
routes.append(Route("/users/{user_id}", get_user_endpoint))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
