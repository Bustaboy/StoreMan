from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore', str_strip_whitespace=True)

    id: str = ''
    code: str = ''
    name: str = ''
    category: str | None = None
    quantity_on_hand: int = 0
    location: str | None = None
    material_number: str = ''
    description: str = ''
    sap_material_number: str | None = None
    is_serialized: bool = False
