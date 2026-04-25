"""
DTO для материалов
"""
from pydantic import BaseModel, Field
from typing import Optional

class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    group_id: Optional[int] = None
    material_group_id: Optional[int] = None # for frontend compatibility
    article: str = Field(..., max_length=100)
    unit_id: int
    min_stock: float = Field(0.0, ge=0)

class MaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    group_id: Optional[int] = None
    article: Optional[str] = Field(None, max_length=100)
    unit_id: Optional[int] = None
    min_stock: Optional[float] = Field(None, ge=0)

class MaterialResponse(BaseModel):
    id: int
    name: str
    group_id: int
    article: str
    unit_id: int
    min_stock: float

    class Config:
        from_attributes = True
