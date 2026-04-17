"""
Интерфейс репозитория для работы с пользователями
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class UserRepositoryInterface(ABC):
    """Интерфейс репозитория пользователей"""
    
    @abstractmethod
    async def get_by_login(self, login: str) -> Optional[Dict]:
        """Получить пользователя по логину"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        pass
    
    @abstractmethod
    async def get_all(self, include_inactive: bool = False) -> List[Dict]:
        """Получить всех пользователей"""
        pass
    
    @abstractmethod
    async def update_last_login(self, user_id: int) -> bool:
        """Обновить время последнего входа"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict:
        """Получить статистику по пользователям"""
        pass