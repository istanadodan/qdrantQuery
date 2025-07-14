from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Integer, select
from sqlalchemy.orm import mapped_column, relationship
from passlib.hash import bcrypt
from typing import List, Optional, Union


class User(BaseModel):
    __tablename__ = "user_tb"

    user_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    username = mapped_column(String(255), nullable=False)
    password = mapped_column(String(255), nullable=False)
    roles = mapped_column(String(10), nullable=False)

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
    ):
        self.user_id = user_id
        self.username = username
        self.password = bcrypt.hash(password)

    def __repr__(self):
        return "<User(user_id='%s')>" % self.user_id

    @staticmethod
    def of(
        user_id: int,
        username: str,
        password: str,
    ):
        return User(
            user_id=user_id,
            username=username,
            password=password,
        )

    def change_password(self, new_password: str, mod_user: "User"):
        self.password = bcrypt.hash(new_password)
        self.mod_user_id = mod_user.id

    def update_roles(self, roles: list[str], mod_user: "User"):
        self.mod_user_id = mod_user.id
        self.roles = roles

    def is_user_password_correct(self, input_password: str) -> bool:
        return bcrypt.verify(input_password, self.password)

    def check_user_active(self):
        if not self.is_active:
            raise Exception(
                code=1, errMsg="User is not active. Please contact to admin."
            )

    def update(
        self,
        mod_user: "User",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        import datetime

        self.name = username if username is not None else self.username
        self.password = bcrypt.hash(password) if password is not None else self.password
        self.mod_user_id = mod_user.id

        if self.reg_user_id is None:
            self.reg_user_id = mod_user.id
            self.reg_date = datetime.datetime.utcnow()

    def activate(self, mod_user: "User"):
        self.reg_user_id = mod_user.id
        self.mod_user_id = mod_user.id

    def delete(self, mod_user: "User"):
        self.mod_user_id = mod_user.id

    @staticmethod
    async def get_by_user_id(user_id: str, session: "AsyncSession") -> "User":

        result = await session.execute(
            select(User).filter_by(user_id=user_id).filter_by(is_deleted=False)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise Exception(code=1, errMsg="User not found.")
        return user
