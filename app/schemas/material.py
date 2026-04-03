from __future__ import annotations

from pydantic import BaseModel, ConfigDict, computed_field


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_number: str
    description: str
    category: str | None
    quantity: int
    location: str | None
    sap_material_number: str | None
    is_serialized: bool

    @computed_field
    @property
    def id(self) -> str:
        return self.material_number

    @computed_field
    @property
    def code(self) -> str:
        return self.material_number

    @computed_field
    @property
    def name(self) -> str:
        return self.description

    @computed_field
    @property
    def quantity_on_hand(self) -> int:
        return self.quantity
