"""
Интерфейс репозитория для материалов
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from application.dto.material_dto import MaterialCreate, MaterialUpdate

class MaterialRepository(ABC):

    @abstractmethod
    async def get_all(self) -> List[dict]:
        pass

    @abstractmethod
    async def get_by_id(self, material_id: int) -> Optional[dict]:
        pass

    @abstractmethod
    async def create(self, material: MaterialCreate) -> int:
        pass

    @abstractmethod
    async def update(self, material_id: int, material: MaterialUpdate) -> bool:
        pass

    @abstractmethod
    async def delete(self, material_id: int) -> bool:
        pass
