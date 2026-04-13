"""
Эндпоинты для авторизации
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import logging

from application.dto.user_dto import LoginRequest, LoginResponse, UserInfo
from infrastructure.auth.password_hasher import password_hasher
from infrastructure.auth.jwt_handler import jwt_handler
from infrastructure.repositories.user_repository import user_repository
from infrastructure.auth.session_manager import session_manager
from api.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """Авторизация пользователя. Возвращает JWT токен."""
    logger.info(f"Login attempt: {login_data.login}")
    
    user = await user_repository.get_by_login(login_data.login)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password"
        )
    
    if not password_hasher.verify_password(login_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password"
        )
    
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Создаём JWT токен
    token = jwt_handler.create_token(
        user_id=user['id'],
        login=user['login'],
        role=user['role'],
        full_name=user.get('full_name')
    )
    
    # Создаём сессию в памяти (с токеном!)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    session_manager.create_session(
        user_id=user['id'],
        token=token,  # ← КЛЮЧЕВОЙ МОМЕНТ!
        login=user['login'],
        role=user['role'],
        full_name=user.get('full_name'),
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Обновляем время последнего входа
    await user_repository.update_last_login(user['id'])
    
    # Очищаем просроченные сессии
    session_manager.cleanup_expired_sessions()
    
    logger.info(f"User {login_data.login} logged in successfully, session created")
    
    return LoginResponse(
        token=token,
        user_id=user['id'],
        login=user['login'],
        role=user['role'],
        full_name=user.get('full_name')
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Информация о текущем пользователе."""
    return UserInfo(
        id=current_user['id'],
        login=current_user['login'],
        role=current_user['role'],
        full_name=current_user.get('full_name')
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user)
):
    """Выход из системы."""
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    
    token = credentials.credentials
    success = session_manager.invalidate_session(token)  # без await
    
    if success:
        logger.info(f"User {current_user['login']} logged out")
        return {"message": "Logged out successfully"}
    
    raise HTTPException(404, "Session not found")


@router.post("/logout/all")
async def logout_all_devices(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Выход на всех устройствах."""
    count = session_manager.invalidate_all_user_sessions(current_user['id'])  # без await
    logger.info(f"User {current_user['login']} logged out from {count} devices")
    return {"message": f"Logged out from {count} devices"}


@router.get("/sessions")
async def get_my_sessions(current_user: dict = Depends(get_current_user)):
    """Список активных сессий."""
    sessions = session_manager.get_active_sessions(current_user['id'])  # без await
    
    result = []
    for session in sessions:
        result.append({
            "id": session['id'],
            "ip_address": session.get('ip_address'),
            "user_agent": session.get('user_agent', '').split('(')[0].strip() if session.get('user_agent') else None,
            "created_at": str(session['created_at']),
            "expires_at": str(session['expires_at'])
        })
    
    return {"sessions": result, "total": len(result)}


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Завершить указанную сессию."""
    # Нельзя завершить текущую сессию
    if session_id == current_user.get('session_id'):
        raise HTTPException(400, "Cannot terminate current session")
    
    success = session_manager.invalidate_session_by_id(session_id)  # без await
    
    if success:
        logger.info(f"Session {session_id} terminated by user {current_user['login']}")
        return {"message": "Session terminated"}
    
    raise HTTPException(404, "Session not found")


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Смена пароля."""
    user = await user_repository.get_by_id(current_user['id'])
    
    if not password_hasher.verify_password(old_password, user['password_hash']):
        raise HTTPException(400, "Wrong old password")
    
    if len(new_password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    
    new_hash = password_hasher.hash_password(new_password)
    success = await user_repository.change_password(current_user['id'], new_hash)
    
    if success:
        # Завершаем все остальные сессии (кроме текущей)
        current_session_id = current_user.get('session_id')
        sessions = session_manager.get_active_sessions(current_user['id'])  # без await
        
        terminated = 0
        for session in sessions:
            if session['id'] != current_session_id:
                session_manager.invalidate_session_by_id(session['id'])  # без await
                terminated += 1
        
        logger.info(f"User {current_user['login']} changed password, terminated {terminated} other sessions")
        
        return {"message": "Password changed", "other_sessions_terminated": terminated}
    
    raise HTTPException(500, "Failed to change password")

# Отладочный вывод
print(f"✅ Auth router: {len(router.routes)} routes registered")
for route in router.routes:
    methods = list(route.methods) if hasattr(route, 'methods') else ['ANY']
    print(f"   {methods[0]:6} {route.path}")