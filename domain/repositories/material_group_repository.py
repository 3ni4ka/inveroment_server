"""
Интерфейс репозитория для работы с группами материалов
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict


class MaterialGroupRepositoryInterface(ABC):
    """Интерфейс репозитория групп материалов"""
    
    @abstractmethod
    async def create(self, name: str, equipment_group_ids: Optional[List[int]] = None) -> int:
        """Создание группы"""
        pass
    
    @abstractmethod
    async def get_by_id(self, group_id: int) -> Optional[Dict]:
        """Получение группы по ID"""
        pass
    
    @abstractmethod
    async def get_all(self, include_children_count: bool = True) -> List[Dict]:
        """Получение всех групп"""
        pass

    @abstractmethod
    async def get_by_equipment_group_id(self, equipment_group_id: int) -> List[Dict]:
        """Получение групп материалов по ID группы оборудования"""
        pass
    
    @abstractmethod
    async def update(
        self,
        group_id: int,
        name: str = None,
        equipment_group_ids: Optional[List[int]] = None,
        update_equipment_groups: bool = False
    ) -> bool:
        """Обновление группы"""
        pass
    
    @abstractmethod
    async def delete(self, group_id: int) -> bool:
        """Удаление группы"""
        pass
    
    @abstractmethod
    async def has_children(self, group_id: int) -> bool:
        """Совместимость: подгруппы не поддерживаются"""
        pass
    
    @abstractmethod
    async def has_materials(self, group_id: int) -> bool:
        """Проверка наличия материалов в группе"""
        pass
    
    @abstractmethod
    async def get_existing_equipment_group_ids(self, equipment_group_ids: List[int]) -> List[int]:
        """Получение существующих equipment_group IDs"""
        pass