from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal

# ============ Auth ============
class LoginRequest(BaseModel):
    login: str
    password: str


class LoginResponse(BaseModel):
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


# ============ Materials ============
class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    article: str = Field(..., min_length=1, max_length=100)
    unit_id: int
    group_id: int
    equipment_group_id: Optional[int] = None
    min_stock: Decimal = Decimal(0)


class MaterialResponse(BaseModel):
    id: int
    name: str
    article: str
    unit_id: int
    unit_name: Optional[str] = None
    group_id: int
    group_name: Optional[str] = None
    min_stock: Decimal


# ============ Stock ============
class StockItemResponse(BaseModel):
    id: int
    name: str
    article: str
    quantity: Decimal
    unit: str
    min_stock: Decimal
    status: str  # 'normal', 'low', 'absent'


# ============ Transactions ============
class TransactionRequest(BaseModel):
    material_id: int
    quantity: Decimal = Field(..., gt=0)
    comment: Optional[str] = ""


class TransactionResponse(BaseModel):
    id: int
    type: str  # 'IN' or 'OUT'
    created_at: datetime
    user_id: int
    user_name: Optional[str] = None
    comment: Optional[str]
    items_count: int
    total_quantity: Decimal
    material_names: Optional[str] = None  # несколько материалов через запятую


class PaginatedTransactionResponse(BaseModel):
    total: int
    page: int
    transactions: list[TransactionResponse]


# ============ Stats ============
class TodayStatsResponse(BaseModel):
    in_count: int
    out_count: int
    in_quantity: Decimal
    out_quantity: Decimal


# ============ Report ============
class PeriodReportRequest(BaseModel):
    date_from: datetime
    date_to: datetime
    material_id: Optional[int] = None