from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_number: str
    description: str
    category: str | None
    quantity: int
    location: str | None
    sap_material_number: str | None
    is_serialized: bool
