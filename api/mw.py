import asyncio
import time
import traceback
from aiohttp import request
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError
import jwt
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import logging
from cmn.token_manage import TokenData
from cmn.context import ApplicationContext
from cmn.user_exception import TimeoutHTTPException


REQUEST_TIMEOUT_SECOD = 10 * 60  # 타임아웃(초)


class TimeoutMonitor:
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
                self.app(scope, receive, send), timeout=REQUEST_TIMEOUT_SECOD
            )
            return response
        except asyncio.TimeoutError:
            process_time = time.time() - start_time
            logging.error(f"타임아웃 발생되어 처리가 종료됩니다.[{process_time}초]")
            traceback.print_exc()
            self.db.rollback()
            return TimeoutHTTPException(process_time=process_time)


exclude_api_list = [
    "user/registration",
    "user/email-duplication",
    "user/user-state",
    "user/send_temp_password",
    "auth/login",
]


class CreateAppContext:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        from core.security import (
            JWT_SECRET,
            ALGORITHM,
        )

        # Gateway에서 Header에 id라는 key로 user_id를 넣어줌. 따라서 AUTHORIZATION을 id로 변경
        AUTHORIZATION = "id"
        user_id = None
        url = scope["path"]  #'/api/v1/ai/doc/summary-streaming'
        # method = scope["method"]  # 'POST'
        headers_map = dict(
            map(
                lambda d: (d[0].decode("utf-8"), d[1].decode("utf-8")), scope["headers"]
            )
        )
        headers_map.update(dict(url=url))

        if (
            AUTHORIZATION in headers_map
            and "/".join(url.split("/")[-2:]) not in exclude_api_list
        ):
            try:
                user_id: str = headers_map[AUTHORIZATION]
            except Exception as e:
                logging.error(f"[토큰 오류]\nheader: {headers_map}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="접속토큰이 유효하지 않습니다. 재로그인하여 주십시오.",
                )

            if user_id:
                # context 생성/갱신.
                context = ApplicationContext(
                    user_id, db=self.db, headers=headers_map, init=True
                )
                # 토큰데이터 초기화 후 생성
                context["token"] = TokenData(user_id=user_id)

                if ApplicationContext.is_expired(user_id):
                    # expire는 1일 기준으로 한다.

                    from service.llm_search.memory import ChatMemory

                    # chat_memory롤 초기화한다.
                    ChatMemory.clear_user_memory(user_id=user_id)

                    # user정보를 취득한다.
                    from crud.crud_user import get_user, create_dto_from_entity

                    try:
                        user_dto = create_dto_from_entity(
                            get_user(self.db, user_id=user_id)
                        )
                        # 회원정보를 갱신한다.
                        context["user_info"] = user_dto
                    except Exception as e:
                        ApplicationContext.dispose_userdata(user_id=user_id, name="all")
                        traceback.print_exc()
                        raise HTTPException(
                            detail="미들웨어 사용자정보 취득에 실패했습니다.",
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                # header 항목추가
                scope["headers"].append((b"user_id", user_id.encode("utf-8")))

                logging.info(f"[토큰 인증]\nuser_id: {user_id},\nheader: {headers_map}")

        # 앱 호출
        await self.app(scope, receive, send)
        return


class LogRequestMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import datetime

        url = scope["path"]  #'/api/v1/ai/doc/summary-streaming'
        method = scope["method"]  # 'POST'
        user_id = scope["headers"]

        log_format = (
            "[{user_id}] {method} {url} {status} {response_time}ms - {content_length}"
        )

        try:
            start_time = datetime.datetime.now()
            response = await self.app(scope, receive, send)
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            user_id = (
                "not_signed"
                if not ApplicationContext.user_data
                else ApplicationContext.headers("user_info").user_id
            )
            data = {
                "user_id": user_id,
                "method": method,
                "url": url,
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
