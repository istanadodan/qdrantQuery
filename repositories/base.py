# repositories/base.py
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from models.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[ModelType]:
        query = db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))

        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.dict()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_batch(
        self, db: Session, *, objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        db_objs = [self.model(**obj_in.dict()) for obj_in in objs_in]
        db.add_all(db_objs)
        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)
        return db_objs

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        query = db.query(self.model)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        return query.count()


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
