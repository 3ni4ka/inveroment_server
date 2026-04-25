"""
Эндпоинты для работы с группами оборудования
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import logging

from application.dto.equipment_group_dto import (
    EquipmentGroupCreate,
    EquipmentGroupUpdate,
    EquipmentGroupResponse
)
from infrastructure.repositories.equipment_group_repository import equipment_group_repository
from api.middleware.auth import get_admin_user, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/equipment-groups", tags=["Equipment Groups"])


@router.get(
    "/",
    response_model=List[EquipmentGroupResponse],
    summary="Список групп оборудования",
    description="Возвращает список всех групп оборудования"
)
async def get_all_equipment_groups(current_user: dict = Depends(get_current_user)):
    """Получить все группы оборудования (требует авторизации)"""
    groups = await equipment_group_repository.get_all()
    return groups


@router.get(
    "/{group_id}",
    response_model=EquipmentGroupResponse,
    summary="Группа оборудования по ID",
    description="Возвращает информацию о группе оборудования"
)
async def get_equipment_group_by_id(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Получить группу по ID (требует авторизации)"""
    group = await equipment_group_repository.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment group with id {group_id} not found"
        )
    return group


# ============ Административные эндпоинты (только admin) ============

@router.post(
    "/",
    response_model=EquipmentGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать группу оборудования",
    description="Создание новой группы оборудования (требует прав администратора)"
)
async def create_equipment_group(
    group_data: EquipmentGroupCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Создать новую группу оборудования (только admin)"""
    try:
        group_id = await equipment_group_repository.create(name=group_data.name)
        new_group = await equipment_group_repository.get_by_id(group_id)
        logger.info(f"Admin {current_user['login']} created equipment group: {group_data.name}")
        return new_group
    except Exception as e:
        logger.error(f"Error creating equipment group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/{group_id}",
    response_model=EquipmentGroupResponse,
    summary="Обновить группу оборудования",
    description="Обновление информации о группе оборудования (требует прав администратора)"
)
async def update_equipment_group(
    group_id: int,
    group_data: EquipmentGroupUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Обновить группу оборудования (только admin)"""
    existing = await equipment_group_repository.get_by_id(group_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment group with id {group_id} not found"
        )

    try:
        success = await equipment_group_repository.update(
            group_id=group_id,
            name=group_data.name
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment group with id {group_id} not found"
            )
        updated_group = await equipment_group_repository.get_by_id(group_id)
        logger.info(f"Admin {current_user['login']} updated equipment group: id={group_id}")
        return updated_group
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating equipment group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{group_id}",
    summary="Удалить группу оборудования",
    description="Удаление группы оборудования (требует прав администратора)"
)
async def delete_equipment_group(
    group_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Удалить группу оборудования (только admin)"""
    existing = await equipment_group_repository.get_by_id(group_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment group with id {group_id} not found"
        )
    try:
        success = await equipment_group_repository.delete(group_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment group with id {group_id} not found"
            )
        logger.info(f"Admin {current_user['login']} deleted equipment group: id={group_id}, name={existing['name']}")
        return {"message": f"Equipment group '{existing['name']}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting equipment group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
