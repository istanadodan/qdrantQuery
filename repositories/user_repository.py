# services/user_service.py
from typing import Optional, List
from sqlalchemy.orm import Session
from models.schemas.user import UserCreate, UserUpdate, User
from managers.database_manager import db_manager
from core.security import verify_password, get_password_hash


class UserService:
    def __init__(self):
        self.repository = db_manager.user

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return self.repository.get(db, user_id)

    def get_users(
        self, db: Session, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[User]:
        filters = {"is_active": True} if active_only else None
        return self.repository.get_multi(db, skip=skip, limit=limit, filters=filters)

    def create_user(self, db: Session, user_in: UserCreate) -> User:
        # 비즈니스 로직 처리
        user_data = user_in.dict()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

        # 이메일 중복 확인
        existing_user = self.repository.get_by_email(db, email=user_data["email"])
        if existing_user:
            raise ValueError("Email already registered")

        return self.repository.create(db, obj_in=UserCreate(**user_data))

    def authenticate_user(
        self, db: Session, email: str, password: str
    ) -> Optional[User]:
        user = self.repository.get_by_email(db, email=email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user


user_service = UserService()
