from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from infrastructure.repositories.unit_repository import UnitRepositoryImpl

router = APIRouter()


class UnitResponse(BaseModel):
    id: int
    name: str
    short_name: str


@router.get("/units", tags=["Units"], response_model=List[UnitResponse])
async def get_units_of_measurement():
    """
    Returns a list of all available units of measurement from the database.
    """
    unit_repository = UnitRepositoryImpl()
    units = await unit_repository.get_all_units()
    return units
