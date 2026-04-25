"""
Эндпоинты для работы с остатками и транзакциями
"""

from fastapi import APIRouter, HTTPException, Depends
from decimal import Decimal
from typing import List, Optional
from datetime import datetime
import logging

from application.dto.schemas import (
    StockItemResponse, 
    TransactionRequest, 
    TransactionResponse,
    PaginatedTransactionResponse
)
from infrastructure.repositories.stock_repository import StockRepository
from infrastructure.repositories.transaction_repository import TransactionRepository
from api.middleware.auth import get_current_user
from utils.event_broadcaster import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Warehouse"])


@router.get(
    "/stock",
    response_model=List[StockItemResponse],
    summary="Остатки материалов",
    description="Возвращает список всех материалов с текущими остатками."
)
async def get_stock(
    only_positive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Получить все остатки материалов (требует авторизации)"""
    repo = StockRepository()
    stock = await repo.get_all_with_details(only_positive)
    logger.info(f"User {current_user['login']} requested stock list")
    return stock


@router.get(
    "/stock/low",
    summary="Критический остаток",
    description="Возвращает материалы, у которых остаток ниже минимального."
)
async def get_low_stock(
    current_user: dict = Depends(get_current_user)
):
    """Получить материалы с остатком ниже минимума"""
    repo = StockRepository()
    low_stock = await repo.get_low_stock()
    logger.info(f"User {current_user['login']} requested low stock list")
    return low_stock


@router.get(
    "/stock/{material_id}",
    summary="Остаток материала",
    description="Возвращает остаток конкретного материала по его ID."
)
async def get_stock_by_material(
    material_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Получить остаток конкретного материала"""
    repo = StockRepository()
    stock = await repo.get_by_material_id(material_id)
    if not stock:
        raise HTTPException(404, f"Material {material_id} not found")
    return stock


@router.post(
    "/material/in",
    summary="Приход материала",
    description="Оприходование материала на склад. Увеличивает остаток."
)
async def material_in(
    request: TransactionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Приход материала"""
    try:
        repo = TransactionRepository()
        trans_id = await repo.create(
            trans_type='IN',
            user_id=current_user['id'],
            material_id=request.material_id,
            quantity=request.quantity,
            comment=request.comment
        )
        logger.info(f"Material IN: user={current_user['login']}, material={request.material_id}, qty={request.quantity}")

        # Broadcast the update via SSE
        stock_repo = StockRepository()
        updated_stock = await stock_repo.get_by_material_id(request.material_id)
        if updated_stock:
            # Convert Decimal to float for JSON serialization
            sse_data = {key: float(value) if isinstance(value, Decimal) else value for key, value in dict(updated_stock).items()}
            await broadcaster.broadcast({
                "event": "stock_update",
                "data": sse_data
            })
            
        return {
            "status": "success",
            "transaction_id": trans_id,
            "message": f"Приход {request.quantity} единиц выполнен"
        }
    except Exception as e:
        logger.error(f"Error in material_in: {e}")
        raise HTTPException(500, str(e))


@router.post(
    "/material/out",
    summary="Расход материала",
    description="Списание материала со склада. Проверяет наличие достаточного остатка."
)
async def material_out(
    request: TransactionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Расход материала с проверкой остатка"""
    try:
        stock_repo = StockRepository()
        current_stock = await stock_repo.get_by_material_id(request.material_id)
        
        if not current_stock:
            raise HTTPException(404, f"Material {request.material_id} not found")
        
        if current_stock['quantity'] < request.quantity:
            raise HTTPException(
                400, 
                f"Недостаточно материала. Доступно: {current_stock['quantity']}, запрошено: {request.quantity}"
            )
        
        repo = TransactionRepository()
        trans_id = await repo.create(
            trans_type='OUT',
            user_id=current_user['id'],
            material_id=request.material_id,
            quantity=request.quantity,
            comment=request.comment
        )
        logger.info(f"Material OUT: user={current_user['login']}, material={request.material_id}, qty={request.quantity}")

        # Broadcast the update via SSE
        updated_stock = await stock_repo.get_by_material_id(request.material_id)
        if updated_stock:
            # Convert Decimal to float for JSON serialization
            sse_data = {key: float(value) if isinstance(value, Decimal) else value for key, value in dict(updated_stock).items()}
            await broadcaster.broadcast({
                "event": "stock_update",
                "data": sse_data
            })
            
        return {
            "status": "success",
            "transaction_id": trans_id,
            "message": f"Расход {request.quantity} единиц выполнен"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in material_out: {e}")
        raise HTTPException(500, str(e))


@router.get(
    "/transactions",
    summary="История операций",
    description="Возвращает список всех операций (приходов и расходов) с пагинацией и фильтрацией.",
    response_model=PaginatedTransactionResponse
)
async def get_transactions(
    page: int = 1,
    limit: int = 50,
    user_id: Optional[int] = None,
    material_id: Optional[int] = None,
    trans_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
):
    """Получить историю операций с фильтрами"""
    repo = TransactionRepository()
    offset = (page - 1) * limit
    transactions = await repo.get_all(
        limit=limit,
        offset=offset,
        user_id=user_id,
        material_id=material_id,
        trans_type=trans_type,
        date_from=date_from,
        date_to=date_to,
    )
    total_count = await repo.get_total_count(
        user_id=user_id,
        material_id=material_id,
        trans_type=trans_type,
        date_from=date_from,
        date_to=date_to,
    )
    logger.info(f"User {current_user['login']} requested transactions history with filters")
    return {
        "total": total_count,
        "page": page,
        "transactions": transactions,
    }


@router.get(
    "/stats/today",
    summary="Статистика за сегодня",
    description="Возвращает количество и сумму приходов/расходов за текущий день."
)
async def get_today_stats(
    current_user: dict = Depends(get_current_user)
):
    """Получить статистику за сегодня"""
    repo = TransactionRepository()
    stats = await repo.get_today_stats()
    return stats