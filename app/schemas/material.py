from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar('T')


class ApiResult(BaseModel, Generic[T]):
    ok: bool = True
    data: T


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_number: str
    description: str
    category: str
    is_serialized: bool
    is_assembly: bool
    min_stock: int | None
    max_stock: int | None
    safety_stock: int | None
    default_location_id: int | None
    is_dangerous_good: bool
    dg_class: str | None
    dg_un_number: str | None
    dg_proper_shipping_name: str | None
    sap_material_number: str | None


class MaterialsPage(BaseModel):
    items: list[MaterialRead]
    limit: int
    offset: int
    total: int
