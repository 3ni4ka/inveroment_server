"""
Интерфейс репозитория для групп оборудования
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class EquipmentGroupRepository(ABC):

    @abstractmethod
    async def get_all(self) -> List[dict]:
        pass

    @abstractmethod
    async def get_by_id(self, group_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    async def create(self, name: str) -> int:
        pass

    @abstractmethod
    async def update(self, group_id: int, name: Optional[str]) -> bool:
        pass

    @abstractmethod
    async def delete(self, group_id: int) -> bool:
        pass
