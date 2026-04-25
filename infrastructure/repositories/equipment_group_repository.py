"""
Репозиторий для работы с группами оборудования (реализация MySQL)
"""

from typing import Optional, List, Dict
import logging
from domain.repositories.equipment_group_repository import EquipmentGroupRepository
from infrastructure.database.connection_pool import database_service

logger = logging.getLogger(__name__)


class EquipmentGroupRepositoryImpl(EquipmentGroupRepository):
    """Реализация EquipmentGroupRepository для MySQL"""

    def __init__(self, db=None):
        self.db = db or database_service

    async def get_all(self) -> List[Dict]:
        """Получение всех групп оборудования"""
        query = "SELECT id, name, created_at FROM equipment_groups ORDER BY id"
        rows = await self.db.fetch_all(query)
        return [dict(row) for row in rows]

    async def get_by_id(self, group_id: int) -> Optional[Dict]:
        """Получение группы оборудования по ID"""
        query = "SELECT id, name, created_at FROM equipment_groups WHERE id = %s"
        row = await self.db.fetch_one(query, (group_id,))
        return dict(row) if row else None

    async def create(self, name: str) -> int:
        """Создание группы оборудования"""
        query = "INSERT INTO equipment_groups (name) VALUES (%s)"
        group_id = await self.db.execute(query, (name,))
        logger.info(f"Equipment group created: id={group_id}, name={name}")
        return int(group_id)

    async def update(self, group_id: int, name: Optional[str]) -> bool:
        """Обновление группы оборудования"""
        if name is None:
            return False # Nothing to update
        query = "UPDATE equipment_groups SET name = %s WHERE id = %s"
        rows_affected = await self.db.execute(query, (name, group_id))
        if rows_affected > 0:
            logger.info(f"Equipment group updated: id={group_id}")
        return rows_affected > 0

    async def delete(self, group_id: int) -> bool:
        """Удаление группы оборудования"""
        # Проверка, связана ли группа с какими-либо группами материалов
        check_query = "SELECT COUNT(*) as count FROM equipment_group_material_groups WHERE equipment_group_id = %s"
        result = await self.db.fetch_one(check_query, (group_id,))
        if result and result['count'] > 0:
            raise ValueError(f"Cannot delete equipment group with id {group_id} as it is linked to material groups.")

        query = "DELETE FROM equipment_groups WHERE id = %s"
        rows_affected = await self.db.execute(query, (group_id,))
        if rows_affected > 0:
            logger.info(f"Equipment group deleted: id={group_id}")
        return rows_affected > 0


# Глобальный экземпляр
equipment_group_repository = EquipmentGroupRepositoryImpl()
