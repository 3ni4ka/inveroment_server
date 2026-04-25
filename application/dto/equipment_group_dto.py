"""
DTO для групп оборудования
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EquipmentGroupCreate(BaseModel):
    """Создание группы оборудования"""
    name: str = Field(..., min_length=1, max_length=255, description="Название группы")


class EquipmentGroupUpdate(BaseModel):
    """Обновление группы оборудования"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название группы")


class EquipmentGroupResponse(BaseModel):
    """Ответ с данными группы оборудования"""
    id: int
    name: str
    created_at: Optional[datetime] = None
