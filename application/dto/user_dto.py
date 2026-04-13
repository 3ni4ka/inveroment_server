"""
DTO для пользователей
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Запрос на логин"""
    login: str
    password: str


class LoginResponse(BaseModel):
    """Ответ на логин"""
    token: str
    user_id: int
    login: str
    role: str
    full_name: Optional[str] = None


class UserInfo(BaseModel):
    """Информация о пользователе"""
    id: int
    login: str
    role: str
    full_name: Optional[str] = None


# ============ DTO для CRUD пользователей ============

class UserCreate(BaseModel):
    """Создание пользователя"""
    login: str = Field(..., min_length=3, max_length=100, description="Логин")
    password: str = Field(..., min_length=4, description="Пароль")
    full_name: str = Field(..., min_length=1, max_length=255, description="ФИО")
    role: str = Field("user", description="Роль: admin или user")


class UserUpdate(BaseModel):
    """Обновление пользователя"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="ФИО")
    role: Optional[str] = Field(None, description="Роль: admin или user")
    is_active: Optional[bool] = Field(None, description="Активен ли пользователь")


class UserChangePassword(BaseModel):
    """Смена пароля (администратором)"""
    new_password: str = Field(..., min_length=4, description="Новый пароль")


class UserResponse(BaseModel):
    """Ответ с данными пользователя (без пароля)"""
    id: int
    login: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Список пользователей"""
    users: list[UserResponse]
    total: int
    active_count: int
    inactive_count: int