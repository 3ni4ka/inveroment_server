from pydantic import BaseModel


class UnitDTO(BaseModel):
    id: int
    name: str
    short_name: str
