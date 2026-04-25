from typing import List

from domain.entities.unit import Unit
from domain.repositories.unit_repository import UnitRepository
from infrastructure.database.connection_pool import database_service


class UnitRepositoryImpl(UnitRepository):
    async def get_all_units(self) -> List[Unit]:
        async with database_service.get_connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT id, name, short_name FROM units")
                rows = await cursor.fetchall()
                return [Unit(id=row[0], name=row[1], short_name=row[2]) for row in rows]
