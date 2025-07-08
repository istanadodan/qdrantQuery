# managers/database_manager.py
from typing import Dict, Type, Any
from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from repositories.vector_repository import VectorRepository


class DatabaseManager:
    def __init__(self):
        self._repositories: Dict[str, Any] = {}
        self._initialize_repositories()

    def _initialize_repositories(self):
        self._repositories["user"] = UserRepository()
        self._repositories["vector"] = VectorRepository()

    def get_repository(self, name: str):
        return self._repositories.get(name)

    @property
    def user(self) -> UserRepository:
        return self._repositories["user"]

    @property
    def vector(self) -> VectorRepository:
        return self._repositories["vector"]


# 전역 매니저 인스턴스
db_manager = DatabaseManager()
