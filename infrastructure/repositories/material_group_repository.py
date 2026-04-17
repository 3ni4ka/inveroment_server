"""
Репозиторий для работы с группами материалов (реализация MySQL)
"""

from typing import Optional, List, Dict
import logging
from domain.repositories.material_group_repository import MaterialGroupRepositoryInterface
from infrastructure.database.connection_pool import database_service

logger = logging.getLogger(__name__)


class MaterialGroupRepository(MaterialGroupRepositoryInterface):
    """Реализация MaterialGroupRepository для MySQL"""

    def __init__(self, db=None):
        self.db = db or database_service

    @staticmethod
    def _row_to_group(row: Dict) -> Dict:
        ids_csv = row.get("equipment_group_ids_csv")
        names_csv = row.get("equipment_group_names_csv")

        equipment_group_ids = [int(x) for x in ids_csv.split(",")] if ids_csv else []
        equipment_group_names = names_csv.split("|||") if names_csv else []
        equipment_groups = []
        for idx, equipment_group_id in enumerate(equipment_group_ids):
            equipment_groups.append({
                "id": equipment_group_id,
                "name": equipment_group_names[idx] if idx < len(equipment_group_names) else ""
            })

        return {
            "id": row["id"],
            "name": row["name"],
            "equipment_group_ids": equipment_group_ids,
            "equipment_groups": equipment_groups,
            "materials_count": int(row.get("materials_count", 0) or 0),
        }

    async def get_existing_equipment_group_ids(self, equipment_group_ids: List[int]) -> List[int]:
        """Получение существующих equipment_group IDs"""
        if not equipment_group_ids:
            return []

        unique_ids = list(dict.fromkeys(equipment_group_ids))
        placeholders = ", ".join(["%s"] * len(unique_ids))
        query = f"SELECT id FROM equipment_groups WHERE id IN ({placeholders})"
        rows = await self.db.fetch_all(query, tuple(unique_ids))
        return [int(row["id"]) for row in rows]

    async def create(self, name: str, equipment_group_ids: Optional[List[int]] = None) -> int:
        """Создание группы"""
        equipment_group_ids = list(dict.fromkeys(equipment_group_ids or []))

        async with self.db.get_connection() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO material_groups (name) VALUES (%s)",
                        (name,)
                    )
                    group_id = cur.lastrowid

                    if equipment_group_ids:
                        values = [(equipment_group_id, group_id) for equipment_group_id in equipment_group_ids]
                        await cur.executemany(
                            """
                            INSERT INTO equipment_group_material_groups (equipment_group_id, material_group_id)
                            VALUES (%s, %s)
                            """,
                            values
                        )

                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

        logger.info(f"Material group created: id={group_id}, name={name}")
        return int(group_id)

    async def get_by_id(self, group_id: int) -> Optional[Dict]:
        """Получение группы по ID"""
        query = """
            SELECT
                mg.id,
                mg.name,
                (
                    SELECT COUNT(*)
                    FROM materials m
                    WHERE m.group_id = mg.id
                ) AS materials_count,
                GROUP_CONCAT(DISTINCT eg.id ORDER BY eg.id) AS equipment_group_ids_csv,
                GROUP_CONCAT(DISTINCT eg.name ORDER BY eg.id SEPARATOR '|||') AS equipment_group_names_csv
            FROM material_groups mg
            LEFT JOIN equipment_group_material_groups egmg ON egmg.material_group_id = mg.id
            LEFT JOIN equipment_groups eg ON eg.id = egmg.equipment_group_id
            WHERE mg.id = %s
            GROUP BY mg.id, mg.name
        """
        row = await self.db.fetch_one(query, (group_id,))
        if not row:
            return None
        return self._row_to_group(row)

    async def get_all(self, include_children_count: bool = True) -> List[Dict]:
        """Получение всех групп"""
        query = """
            SELECT
                mg.id,
                mg.name,
                (
                    SELECT COUNT(*)
                    FROM materials m
                    WHERE m.group_id = mg.id
                ) AS materials_count,
                GROUP_CONCAT(DISTINCT eg.id ORDER BY eg.id) AS equipment_group_ids_csv,
                GROUP_CONCAT(DISTINCT eg.name ORDER BY eg.id SEPARATOR '|||') AS equipment_group_names_csv
            FROM material_groups mg
            LEFT JOIN equipment_group_material_groups egmg ON egmg.material_group_id = mg.id
            LEFT JOIN equipment_groups eg ON eg.id = egmg.equipment_group_id
            GROUP BY mg.id, mg.name
            ORDER BY mg.id
        """
        rows = await self.db.fetch_all(query)
        return [self._row_to_group(row) for row in rows]

    async def get_by_equipment_group_id(self, equipment_group_id: int) -> List[Dict]:
        """Получение групп материалов по ID группы оборудования"""
        query = """
            SELECT
                mg.id,
                mg.name,
                (
                    SELECT COUNT(*)
                    FROM materials m
                    WHERE m.group_id = mg.id
                ) AS materials_count,
                GROUP_CONCAT(DISTINCT eg.id ORDER BY eg.id) AS equipment_group_ids_csv,
                GROUP_CONCAT(DISTINCT eg.name ORDER BY eg.id SEPARATOR '|||') AS equipment_group_names_csv
            FROM material_groups mg
            INNER JOIN equipment_group_material_groups egmg ON egmg.material_group_id = mg.id
            LEFT JOIN equipment_groups eg ON eg.id = egmg.equipment_group_id
            WHERE mg.id IN (
                SELECT material_group_id
                FROM equipment_group_material_groups
                WHERE equipment_group_id = %s
            )
            GROUP BY mg.id, mg.name
            ORDER BY mg.id
        """
        rows = await self.db.fetch_all(query, (equipment_group_id,))
        return [self._row_to_group(row) for row in rows]

    async def update(
        self,
        group_id: int,
        name: str = None,
        equipment_group_ids: Optional[List[int]] = None,
        update_equipment_groups: bool = False
    ) -> bool:
        """Обновление группы"""
        updated = False
        normalized_equipment_group_ids = list(dict.fromkeys(equipment_group_ids or []))

        async with self.db.get_connection() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cur:
                    if name is not None:
                        rows = await cur.execute(
                            "UPDATE material_groups SET name = %s WHERE id = %s",
                            (name, group_id)
                        )
                        updated = updated or rows > 0

                    if update_equipment_groups:
                        await cur.execute(
                            "DELETE FROM equipment_group_material_groups WHERE material_group_id = %s",
                            (group_id,)
                        )
                        if normalized_equipment_group_ids:
                            values = [(equipment_group_id, group_id) for equipment_group_id in normalized_equipment_group_ids]
                            await cur.executemany(
                                """
                                INSERT INTO equipment_group_material_groups (equipment_group_id, material_group_id)
                                VALUES (%s, %s)
                                """,
                                values
                            )
                        updated = True

                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

        logger.info(f"Material group updated: id={group_id}")
        return updated

    async def delete(self, group_id: int) -> bool:
        """Удаление группы"""
        if await self.has_materials(group_id):
            raise ValueError("Cannot delete group that has materials")

        async with self.db.get_connection() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM equipment_group_material_groups WHERE material_group_id = %s",
                        (group_id,)
                    )
                    rows = await cur.execute("DELETE FROM material_groups WHERE id = %s", (group_id,))
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

        if rows > 0:
            logger.info(f"Material group deleted: id={group_id}")
        return rows > 0

    async def has_children(self, group_id: int) -> bool:
        """Совместимость: подгруппы не поддерживаются"""
        return False

    async def has_materials(self, group_id: int) -> bool:
        """Проверка наличия материалов в группе"""
        query = "SELECT COUNT(*) as count FROM materials WHERE group_id = %s"
        result = await self.db.fetch_one(query, (group_id,))
        return result["count"] > 0 if result else False


# Глобальный экземпляр
material_group_repository = MaterialGroupRepository()