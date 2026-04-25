"""
DTO для групп материалов
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MaterialGroupCreate(BaseModel):
    """Создание группы материалов"""
    name: str = Field(..., min_length=1, max_length=255, description="Название группы")
    equipment_group_ids: List[int] = Field(default_factory=list, description="ID групп оборудования")


class MaterialGroupUpdate(BaseModel):
    """Обновление группы материалов"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название группы")
    equipment_group_ids: Optional[List[int]] = Field(None, description="ID групп оборудования")
    equipment_group_id: Optional[int] = Field(None, description="ID группы оборудования (для совместимости)")


class EquipmentGroupRef(BaseModel):
    """Краткая информация о группе оборудования"""
    id: int
    name: str


class MaterialGroupResponse(BaseModel):
    """Ответ с данными группы материалов"""
    id: int
    name: str
    equipment_group_ids: List[int] = Field(default_factory=list)
    equipment_groups: List[EquipmentGroupRef] = Field(default_factory=list)
    materials_count: int = 0
    created_at: Optional[datetime] = None