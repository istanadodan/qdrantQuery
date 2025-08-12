import uvicorn
from dotenv import load_dotenv
from core.logging import setup_logging, logging

load_dotenv()

# 로깅 설정
setup_logging()

logger = logging.getLogger(__name__)

bootstrap_servers = "localhost:9092"


def create_app():
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    from core.middleware import add_middleware
    from api.v1 import api_route

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from core.database import check_db_connection
        from services.kafka import KafkaInfluenceConsumer

        await check_db_connection()

        consumer = KafkaInfluenceConsumer(
            topics=["my-topic"],
            group_id="test-group",
            bootstrap_servers=bootstrap_servers,
        )

        def test_handler(t):
            logger.info(f"consumer one {t}")

        consumer.consume_messages(message_handler=test_handler)
        yield

    # app설정
    app = FastAPI(title="test api", lifespan=lifespan)

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
    add_middleware(app)

    # db = next(get_db())
    # app.add_middleware(TimeoutMonitor, db=db)
    # app.add_middleware(CreateAppContext, db=db)

    # app.add_middleware(LogRequestMiddleware)
    return app


if __name__ == "__main__":
    # 설정값 로딩
    app = create_app()
    uvicorn.run(app, host="localhost", port=8000)
