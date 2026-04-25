"""
Интерфейс репозитория для работы с транзакциями
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from decimal import Decimal


class TransactionRepositoryInterface(ABC):
    """Интерфейс репозитория транзакций"""
    
    @abstractmethod
    async def create(self, trans_type: str, user_id: int, 
                     material_id: int, quantity: Decimal, 
                     comment: str = "") -> int:
        """Создать транзакцию"""
        pass
    
    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
        material_id: Optional[int] = None,
        trans_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Dict]:
        """Получить все транзакции"""
        pass
    

    @abstractmethod
    async def get_today_stats(self) -> Dict:
        """Получить статистику за сегодня"""
        pass

    @abstractmethod
    async def get_total_count(
        self,
        user_id: Optional[int] = None,
        material_id: Optional[int] = None,
        trans_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """Получить общее количество транзакций"""
        pass