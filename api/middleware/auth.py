"""
Middleware для проверки JWT токена
"""

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from infrastructure.auth.jwt_handler import jwt_handler
from infrastructure.auth.session_manager import session_manager

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Получение текущего пользователя из JWT токена.
    
    Поддерживает два способа передачи токена:
    1. Заголовок: Authorization: Bearer <token>
    2. Query параметр: ?token=<token> (для SSE)
    """
    token = None
    
    # 1. Пробуем получить из заголовка Authorization
    if credentials:
        token = credentials.credentials
    
    # 2. Если нет в заголовке, пробуем из query параметра
    if not token:
        token = request.query_params.get('token')
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Проверяем JWT токен
    payload = jwt_handler.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. Проверяем сессию в памяти
    session = session_manager.validate_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": session['user_id'],
        "login": session['login'],
        "role": session['role'],
        "full_name": session.get('full_name'),
        "session_id": session.get('session_id')
    }


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Только администратор"""
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin rights required"
        )
    return current_user