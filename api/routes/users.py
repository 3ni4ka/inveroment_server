"""
Эндпоинты для управления пользователями (только администратор)
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import logging

from application.dto.user_dto import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserChangePassword
)
from infrastructure.repositories.user_repository import user_repository
from infrastructure.auth.password_hasher import password_hasher
from api.middleware.auth import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Список пользователей",
    description="Возвращает список всех пользователей (только для администратора)"
)
async def get_all_users(
    include_inactive: bool = False,
    current_user: dict = Depends(get_admin_user)
):
    """Получить всех пользователей"""
    users_data = await user_repository.get_all(include_inactive=include_inactive)
    stats = await user_repository.get_stats()
    
    return UserListResponse(
        users=[UserResponse(**u) for u in users_data],
        total=stats.get('total', 0),
        active_count=stats.get('active', 0),
        inactive_count=stats.get('inactive', 0)
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Пользователь по ID",
    description="Возвращает информацию о пользователе (только для администратора)"
)
async def get_user_by_id(
    user_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Получить пользователя по ID"""
    user = await user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return UserResponse(**user)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    description="Создание нового пользователя (только для администратора)"
)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Создать нового пользователя"""
    # Проверяем, не существует ли пользователь с таким логином
    existing = await user_repository.get_by_login(user_data.login)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with login '{user_data.login}' already exists"
        )
    
    # Проверяем роль
    if user_data.role not in ['admin', 'user']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'user'"
        )
    
    # Проверяем длину пароля
    if len(user_data.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters"
        )
    
    # Хешируем пароль
    password_hash = password_hasher.hash_password(user_data.password)
    
    # Создаём пользователя
    user_id = await user_repository.create(
        login=user_data.login,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    if user_id:
        logger.info(f"Admin {current_user['login']} created user: {user_data.login}")
        return {
            "message": f"User '{user_data.login}' created successfully",
            "success": True,
            "user_id": user_id
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put(
    "/{user_id}",
    summary="Обновить пользователя",
    description="Обновление информации о пользователе (только для администратора)"
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Обновить пользователя"""
    # Проверяем существование
    existing = await user_repository.get_by_id(user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Нельзя деактивировать самого себя
    if user_data.is_active is False and user_id == current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Обновляем
    success = await user_repository.update(
        user_id=user_id,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=user_data.is_active
    )
    
    if success:
        logger.info(f"Admin {current_user['login']} updated user: id={user_id}")
        return {
            "message": "User updated successfully",
            "success": True
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )


@router.delete(
    "/{user_id}",
    summary="Мягкое удаление пользователя",
    description="Деактивирует пользователя (is_active = false). Пользователь не может войти в систему."
)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Мягкое удаление пользователя"""
    # Проверяем существование
    existing = await user_repository.get_by_id(user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Нельзя удалить самого себя
    if user_id == current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Нельзя удалить последнего администратора
    if existing['role'] == 'admin':
        all_users = await user_repository.get_all(include_inactive=False)
        active_admins = [u for u in all_users if u['role'] == 'admin' and u['id'] != user_id]
        if len(active_admins) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last active admin"
            )
    
    # Мягкое удаление
    success = await user_repository.delete(user_id)
    
    if success:
        logger.info(f"Admin {current_user['login']} deactivated user: {existing['login']}")
        return {
            "message": f"User '{existing['login']}' has been deactivated",
            "success": True,
            "user_id": user_id
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )


@router.post(
    "/{user_id}/restore",
    summary="Восстановить пользователя",
    description="Активирует пользователя (is_active = true)"
)
async def restore_user(
    user_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Восстановление пользователя"""
    existing = await user_repository.get_by_id(user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    if existing['is_active']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )
    
    success = await user_repository.restore(user_id)
    
    if success:
        logger.info(f"Admin {current_user['login']} restored user: {existing['login']}")
        return {
            "message": f"User '{existing['login']}' has been restored",
            "success": True,
            "user_id": user_id
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )


@router.post(
    "/{user_id}/reset-password",
    summary="Сбросить пароль",
    description="Сброс пароля пользователя (только для администратора)"
)
async def reset_user_password(
    user_id: int,
    password_data: UserChangePassword,
    current_user: dict = Depends(get_admin_user)
):
    """Сброс пароля пользователя"""
    existing = await user_repository.get_by_id(user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Проверяем длину пароля
    if len(password_data.new_password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters"
        )
    
    # Хешируем новый пароль
    new_hash = password_hasher.hash_password(password_data.new_password)
    
    success = await user_repository.change_password(user_id, new_hash)
    
    if success:
        # Завершаем все сессии пользователя (чтобы пришлось войти заново)
        from infrastructure.auth.session_manager import session_manager
        session_manager.invalidate_all_user_sessions(user_id)
        
        logger.info(f"Admin {current_user['login']} reset password for user: {existing['login']}")
        
        return {
            "message": f"Password reset for user '{existing['login']}'",
            "success": True,
            "new_password": password_data.new_password
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.get(
    "/stats/summary",
    summary="Статистика пользователей",
    description="Возвращает статистику по пользователям"
)
async def get_users_stats(
    current_user: dict = Depends(get_admin_user)
):
    """Получить статистику пользователей"""
    stats = await user_repository.get_stats()
    return stats