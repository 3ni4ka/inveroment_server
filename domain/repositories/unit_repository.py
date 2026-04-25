from abc import ABC, abstractmethod
from typing import List

from domain.entities.unit import Unit


class UnitRepository(ABC):
    @abstractmethod
    async def get_all_units(self) -> List[Unit]:
        pass
