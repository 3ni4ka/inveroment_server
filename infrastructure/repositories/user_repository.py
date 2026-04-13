"""
Репозиторий для работы с пользователями (реализация MySQL)
"""

from typing import Optional, Dict, List
import logging
from domain.repositories.user_repository import UserRepositoryInterface
from infrastructure.database.connection_pool import database_service
from infrastructure.auth.password_hasher import password_hasher

logger = logging.getLogger(__name__)


class UserRepository(UserRepositoryInterface):
    """Реализация UserRepository для MySQL"""
    
    def __init__(self, db=None):
        self.db = db or database_service
    
    async def get_by_login(self, login: str) -> Optional[Dict]:
        """Получить пользователя по логину"""
        query = """
            SELECT id, login, full_name, password_hash, role, is_active, created_at, last_login
            FROM users
            WHERE login = %s
        """
        return await self.db.fetch_one(query, (login,))
    
    async def get_by_id(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        query = """
            SELECT id, login, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE id = %s
        """
        result = await self.db.fetch_one(query, (user_id,))
        logger.info(f"get_by_id({user_id}) result: {result}")
        return result
    
    async def get_all(self, include_inactive: bool = False) -> List[Dict]:
        """Получить всех пользователей"""
        if include_inactive:
            query = """
                SELECT id, login, full_name, role, is_active, created_at, last_login
                FROM users
                ORDER BY id
            """
        else:
            query = """
                SELECT id, login, full_name, role, is_active, created_at, last_login
                FROM users
                WHERE is_active = 1
                ORDER BY id
            """
        return await self.db.fetch_all(query)
    
    async def create(self, login: str, password_hash: str, full_name: str, role: str = "user") -> int:
        """Создание пользователя"""
        try:
            query = """
                INSERT INTO users (login, password_hash, full_name, role, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """
            # Выполняем вставку и получаем ID
            async with self.db.transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, (login, password_hash, full_name, role))
                    user_id = cur.lastrowid
                    
                    if user_id and user_id > 0:
                        logger.info(f"User created with id: {user_id}, login: {login}")
                        return user_id
                    
                    # Если lastrowid не сработал
                    await cur.execute("SELECT LAST_INSERT_ID()")
                    row = await cur.fetchone()
                    if row:
                        user_id = row[0] if isinstance(row, (tuple, list)) else row.get('id', 0)
                        if user_id:
                            logger.info(f"User created with id (SELECT): {user_id}, login: {login}")
                            return user_id
            
            # Если всё else не сработало, получаем через отдельный запрос
            result = await self.db.fetch_one("SELECT LAST_INSERT_ID() as id")
            if result:
                if isinstance(result, dict):
                    user_id = result.get('id', 0)
                elif isinstance(result, (tuple, list)):
                    user_id = result[0] if len(result) > 0 else 0
                else:
                    user_id = 0
                
                if user_id:
                    logger.info(f"User created with id (fetch_one): {user_id}, login: {login}")
                    return user_id
            
            # Последняя попытка - найти пользователя по логину
            user = await self.get_by_login(login)
            if user and user.get('id'):
                user_id = user['id']
                logger.info(f"User found by login: id={user_id}")
                return user_id
            
            logger.error(f"Failed to get insert id for user: {login}")
            return 0
            
        except Exception as e:
            logger.error(f"Error creating user {login}: {e}")
            raise
    
    async def update(self, user_id: int, full_name: str = None, role: str = None, is_active: bool = None) -> bool:
        """Обновление пользователя"""
        updates = []
        params = []
        
        if full_name is not None:
            updates.append("full_name = %s")
            params.append(full_name)
        
        if role is not None:
            if role not in ['admin', 'user']:
                raise ValueError("Role must be 'admin' or 'user'")
            updates.append("role = %s")
            params.append(role)
        
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)
        
        if not updates:
            return True
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        params.append(user_id)
        
        rows = await self.db.execute(query, tuple(params))
        logger.info(f"User updated: id={user_id}, rows={rows}")
        return rows > 0
    
    async def delete(self, user_id: int) -> bool:
        """Мягкое удаление (установка is_active = False)"""
        return await self.update(user_id, is_active=False)
    
    async def restore(self, user_id: int) -> bool:
        """Восстановление пользователя (установка is_active = True)"""
        return await self.update(user_id, is_active=True)
    
    async def change_password(self, user_id: int, new_password_hash: str) -> bool:
        """Смена пароля"""
        query = "UPDATE users SET password_hash = %s WHERE id = %s"
        rows = await self.db.execute(query, (new_password_hash, user_id))
        return rows > 0
    
    async def update_last_login(self, user_id: int) -> bool:
        """Обновить время последнего входа"""
        query = "UPDATE users SET last_login = NOW() WHERE id = %s"
        rows = await self.db.execute(query, (user_id,))
        return rows > 0
    
    async def get_stats(self) -> Dict:
        """Получить статистику по пользователям"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admins,
                SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as users
            FROM users
        """
        result = await self.db.fetch_one(query)
        return result or {'total': 0, 'active': 0, 'inactive': 0, 'admins': 0, 'users': 0}


# Глобальный экземпляр
user_repository = UserRepository()