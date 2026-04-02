from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar('T')


class ApiResult(BaseModel, Generic[T]):
    ok: bool = True
    data: T


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_number: str
    description: str
    category: str
    sap_material_number: str | None
