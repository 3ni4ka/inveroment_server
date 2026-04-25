"""
Эндпоинты для работы с материалами
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import logging

from application.dto.material_dto import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse
)
from infrastructure.repositories.material_repository import material_repository
from api.middleware.auth import get_admin_user, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/materials", tags=["Materials"])


@router.get(
    "/",
    response_model=List[MaterialResponse],
    summary="Список материалов",
    description="Возвращает список всех материалов"
)
async def get_all_materials(current_user: dict = Depends(get_current_user)):
    """Получить все материалы (требует авторизации)"""
    materials = await material_repository.get_all()
    return materials


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Материал по ID",
    description="Возвращает информацию о материале"
)
async def get_material_by_id(
    material_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Получить материал по ID (требует авторизации)"""
    material = await material_repository.get_by_id(material_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material with id {material_id} not found"
        )
    return material


# ============ Административные эндпоинты (только admin) ============

@router.post(
    "/",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать материал",
    description="Создание нового материала (требует прав администратора)"
)
async def create_material(
    material_data: MaterialCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Создать новый материал (только admin)"""
    # Handle frontend compatibility for group_id
    if material_data.group_id is None:
        material_data.group_id = material_data.material_group_id

    # If still no group_id, raise validation error
    if material_data.group_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{'type': 'missing', 'loc': ['body', 'group_id'], 'msg': 'Field required'}]
        )

    try:
        material_id = await material_repository.create(material_data)
        new_material = await material_repository.get_by_id(material_id)
        logger.info(f"Admin {current_user['login']} created material: {material_data.name}")
        return new_material
    except Exception as e:
        logger.error(f"Error creating material: {e}")
        # Check for foreign key violation to give a more specific error
        if "foreign key constraint" in str(e).lower():
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material group with id {material_data.group_id} not found."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Обновить материал",
    description="Обновление информации о материале (требует прав администратора)"
)
async def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Обновить материал (только admin)"""
    existing = await material_repository.get_by_id(material_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material with id {material_id} not found"
        )

    try:
        success = await material_repository.update(material_id, material_data)
        if not success:
            # This might happen if the update results in no change, which is not an error
            # So we just return the existing data
            return existing
        updated_material = await material_repository.get_by_id(material_id)
        logger.info(f"Admin {current_user['login']} updated material: id={material_id}")
        return updated_material
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating material: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{material_id}",
    summary="Удалить материал",
    description="Удаление материала (требует прав администратора)"
)
async def delete_material(
    material_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Удалить материал (только admin)"""
    existing = await material_repository.get_by_id(material_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material with id {material_id} not found"
        )
    try:
        success = await material_repository.delete(material_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with id {material_id} not found"
            )
        logger.info(f"Admin {current_user['login']} deleted material: id={material_id}, name={existing['name']}")
        return {"message": f"Material '{existing['name']}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting material: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
