"""
Репозиторий для работы с материалами (реализация MySQL)
"""

from typing import Optional, List, Dict
import logging
from domain.repositories.material_repository import MaterialRepository
from infrastructure.database.connection_pool import database_service
from application.dto.material_dto import MaterialCreate, MaterialUpdate

logger = logging.getLogger(__name__)

class MaterialRepositoryImpl(MaterialRepository):
    """Реализация MaterialRepository для MySQL"""

    def __init__(self, db=None):
        self.db = db or database_service

    async def get_all(self) -> List[Dict]:
        """Получение всех материалов"""
        query = "SELECT id, name, group_id, article, unit_id, min_stock FROM materials ORDER BY id"
        rows = await self.db.fetch_all(query)
        return [dict(row) for row in rows]

    async def get_by_id(self, material_id: int) -> Optional[Dict]:
        """Получение материала по ID"""
        query = "SELECT id, name, group_id, article, unit_id, min_stock FROM materials WHERE id = %s"
        row = await self.db.fetch_one(query, (material_id,))
        return dict(row) if row else None

    async def create(self, material: MaterialCreate) -> int:
        """Создание материала"""
        query = "INSERT INTO materials (name, group_id, article, unit_id, min_stock) VALUES (%s, %s, %s, %s, %s)"
        material_id = await self.db.execute(query, (material.name, material.group_id, material.article, material.unit_id, material.min_stock))
        logger.info(f"Material created: id={material_id}, name={material.name}")
        return int(material_id)

    async def update(self, material_id: int, material: MaterialUpdate) -> bool:
        """Обновление материала"""
        updates = []
        params = []
        if material.name is not None:
            updates.append("name = %s")
            params.append(material.name)
        if material.group_id is not None:
            updates.append("group_id = %s")
            params.append(material.group_id)
        if "article" in material.model_fields_set:
            updates.append("article = %s")
            params.append(material.article)
        if material.unit_id is not None:
            updates.append("unit_id = %s")
            params.append(material.unit_id)
        if material.min_stock is not None:
            updates.append("min_stock = %s")
            params.append(material.min_stock)

        if not updates:
            return False # Nothing to update

        query = f"UPDATE materials SET {', '.join(updates)} WHERE id = %s"
        params.append(material_id)
        rows_affected = await self.db.execute(query, tuple(params))
        if rows_affected > 0:
            logger.info(f"Material updated: id={material_id}")
        return rows_affected > 0

    async def delete(self, material_id: int) -> bool:
        """Удаление материала"""
        # Add check for stock before deleting
        # query_stock = "SELECT COUNT(*) as count FROM stock WHERE material_id = %s"
        # stock_result = await self.db.fetch_one(query_stock, (material_id,))
        # if stock_result['count'] > 0:
        #     raise ValueError(f"Cannot delete material with id {material_id} as it has stock records.")

        query = "DELETE FROM materials WHERE id = %s"
        rows_affected = await self.db.execute(query, (material_id,))
        if rows_affected > 0:
            logger.info(f"Material deleted: id={material_id}")
        return rows_affected > 0

# Глобальный экземпляр
material_repository = MaterialRepositoryImpl()
