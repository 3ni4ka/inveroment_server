"""
Эндпоинты для работы с группами материалов
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import logging

from application.dto.material_group_dto import (
    MaterialGroupCreate,
    MaterialGroupUpdate,
    MaterialGroupResponse
)
from infrastructure.repositories.material_group_repository import material_group_repository
from api.middleware.auth import get_admin_user, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/material-groups", tags=["Material Groups"])
equipment_router = APIRouter(prefix="/api/equipment-groups", tags=["Material Groups"])


@router.get(
    "/",
    response_model=List[MaterialGroupResponse],
    summary="Список групп",
    description="Возвращает список всех групп материалов"
)
async def get_all_groups(current_user: dict = Depends(get_current_user)):
    """Получить все группы материалов (требует авторизации)"""
    groups = await material_group_repository.get_all()
    return groups


@equipment_router.get(
    "/{equipment_group_id}/material-groups",
    response_model=List[MaterialGroupResponse],
    summary="Группы материалов по группе оборудования",
    description="Возвращает список групп материалов, привязанных к указанной группе оборудования"
)
async def get_material_groups_by_equipment_group(
    equipment_group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Получить группы материалов по ID группы оборудования (требует авторизации)"""
    existing_equipment_group_ids = await material_group_repository.get_existing_equipment_group_ids([equipment_group_id])
    if not existing_equipment_group_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment group with id {equipment_group_id} not found"
        )

    groups = await material_group_repository.get_by_equipment_group_id(equipment_group_id)
    return groups


@router.get(
    "/{group_id}",
    response_model=MaterialGroupResponse,
    summary="Группа по ID",
    description="Возвращает информацию о группе материалов"
)
async def get_group_by_id(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Получить группу по ID (требует авторизации)"""
    group = await material_group_repository.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with id {group_id} not found"
        )
    return group


# ============ Административные эндпоинты (только admin) ============

@router.post(
    "/",
    response_model=MaterialGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать группу",
    description="Создание новой группы материалов (требует прав администратора)"
)
async def create_group(
    group_data: MaterialGroupCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Создать новую группу материалов (только admin)"""
    try:
        existing_equipment_group_ids = await material_group_repository.get_existing_equipment_group_ids(
            group_data.equipment_group_ids
        )
        missing_equipment_group_ids = sorted(set(group_data.equipment_group_ids) - set(existing_equipment_group_ids))
        if missing_equipment_group_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment groups not found: {missing_equipment_group_ids}"
            )
        
        group_id = await material_group_repository.create(
            name=group_data.name,
            equipment_group_ids=group_data.equipment_group_ids
        )
        
        new_group = await material_group_repository.get_by_id(group_id)
        
        logger.info(f"Admin {current_user['login']} created material group: {group_data.name}")
        
        return new_group
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/{group_id}",
    response_model=MaterialGroupResponse,
    summary="Обновить группу",
    description="Обновление информации о группе (требует прав администратора)"
)
async def update_group(
    group_id: int,
    group_data: MaterialGroupUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Обновить группу материалов (только admin)"""
    existing = await material_group_repository.get_by_id(group_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with id {group_id} not found"
        )
    
    update_equipment_groups = "equipment_group_ids" in group_data.model_fields_set
    new_equipment_group_ids = group_data.equipment_group_ids if update_equipment_groups else None

    if update_equipment_groups:
        existing_equipment_group_ids = await material_group_repository.get_existing_equipment_group_ids(
            new_equipment_group_ids or []
        )
        missing_equipment_group_ids = sorted(set(new_equipment_group_ids or []) - set(existing_equipment_group_ids))
        if missing_equipment_group_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment groups not found: {missing_equipment_group_ids}"
            )
    
    try:
        success = await material_group_repository.update(
            group_id=group_id,
            name=group_data.name,
            equipment_group_ids=new_equipment_group_ids,
            update_equipment_groups=update_equipment_groups
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with id {group_id} not found"
            )
        
        updated_group = await material_group_repository.get_by_id(group_id)
        
        logger.info(f"Admin {current_user['login']} updated material group: id={group_id}")
        
        return updated_group
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{group_id}",
    summary="Удалить группу",
    description="Удаление группы материалов (требует прав администратора)"
)
async def delete_group(
    group_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Удалить группу материалов (только admin)"""
    existing = await material_group_repository.get_by_id(group_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with id {group_id} not found"
        )
    
    try:
        success = await material_group_repository.delete(group_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with id {group_id} not found"
            )
        
        logger.info(f"Admin {current_user['login']} deleted material group: id={group_id}, name={existing['name']}")
        
        return {"message": f"Group '{existing['name']}' deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )