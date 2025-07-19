from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str


class User(BaseModel):
    user_id: int
    username: str
    password: str
    roles: str
    reg_date: datetime
    mod_date: datetime

    class Config:
        from_attributes = True


class User1(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int
    role: UserRole
    is_active: bool = True
    address: Optional[Address] = None
    tags: List[str] = []
    created_at: datetime

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


def test():
    # 사용 예제
    user_data = {
        "id": 1,
        "name": "김철수",
        "email": "kim@example.com",
        "age": 30,
        "role": "admin",
        "address": {
            "street": "강남대로 123",
            "city": "서울",
            "country": "대한민국",
            "postal_code": "12345",
        },
        "tags": ["developer", "python"],
        "created_at": "2024-01-15T10:30:00",
    }

    # 자동 타입 변환 및 검증
    user = User1(**user_data)
    print(user.model_dump_json(indent=2))

    # 잘못된 데이터로 검증 테스트
    try:
        invalid_user = User(
            id="not_a_number",  # 자동으로 int로 변환 시도
            name="",  # 검증 실패
            email="invalid_email",  # 이메일 형식 검증 실패
            age=-5,  # 나이 검증 실패
            role="invalid_role",  # Enum 검증 실패
            created_at="2024-01-15T10:30:00",
        )
    except Exception as e:
        print(f"Validation Error: {e}")
