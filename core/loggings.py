import logging
from pathlib import Path
import datetime


class Logger:
    # 로그출력 포맷 작성
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    root_dir = Path("/logs")
    _logger = None

    @classmethod
    def setup(cls):
        cls()

    @classmethod
    def getLogger(cls, name, level=logging.INFO):
        if cls._logger is None:
            Logger.setup()
        return cls._logger.getLogger(name, level)

    def __init__(self, level=logging.DEBUG) -> None:
        from logging.handlers import RotatingFileHandler

        # 로깅폴더 초기화
        self.root_dir.mkdir(exist_ok=True)

        # 루트 로거 설정
        __logger = logging.getLogger()
        __logger.setLevel(level)

        file_log_handler = RotatingFileHandler(
            filename=self.root_dir / self._log_filename(),
            backupCount=30,
            maxBytes=10 * 1024 * 1024,  # 10MB
            encoding="utf-8",
        )
        file_log_handler.setFormatter(self.__logging_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.__logging_formatter)

        # 출력 설정; 기존에 추가된 핸들러가 있다면 제거 (중복 로깅 방지)
        if __logger.hasHandlers():
            __logger.handlers.clear()
        # for handler in logging.handlers[:]:
        #     __logger.removeHandler(handler)

        __logger.addHandler(file_log_handler)
        __logger.addHandler(console_handler)
        Logger._logger = __logger

        #     (Safety Net) `sys.excepthook`: 미들웨어가 잡지 못하는 영역(백그라운드, 시작/종료 등)에서 발생하는 예외를 놓치지 않고
        #   로그로 남기기 위한 안전망(Safety Net)으로 함께 사용합니다.
        # Uncaught Exception에 대한 로깅 핸들러 설정
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # KeyboardInterrupt는 기본 동작을 따르도록 함
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            __logger.critical(
                "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
            )

        import sys

        sys.excepthook = handle_exception

    @property
    def __logging_formatter(self) -> logging.Formatter:
        return logging.Formatter(
            self.log_format,
            datefmt=self.date_format,
        )

    def _log_filename(self) -> str:
        return f"prj_{datetime.datetime.now().strftime(self.date_format)}.log"
