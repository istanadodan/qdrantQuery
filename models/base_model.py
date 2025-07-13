from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, relationship, declared_attr

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_active = mapped_column(Integer, nullable=False, default=True)
    reg_user_id = mapped_column(Integer, ForeignKey("user_tb.id"))
    mod_user_id = mapped_column(Integer, ForeignKey("user_tb.id"))

    @declared_attr
    def reg_user(self):
        return relationship(
            "User", uselist=False, foreign_keys=[self.reg_user_id], lazy="selectin"
        )

    @declared_attr
    def mod_user(self):
        return relationship(
            "User", uselist=False, foreign_keys=[self.mod_user_id], lazy="selectin"
        )

    reg_date = mapped_column(
        DateTime(timezone=True), default=func.current_timestamp(), nullable=False
    )
    mod_date = mapped_column(
        DateTime(timezone=True),
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )


class BaseModel2(Base):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    reg_user_id = mapped_column(Integer, ForeignKey("user_tb.id"))

    @declared_attr
    def reg_user(self):
        return relationship(
            "User", uselist=False, foreign_keys=[self.reg_user_id], lazy="selectin"
        )

    reg_date = mapped_column(
        DateTime(timezone=True), default=func.current_timestamp(), nullable=False
    )
