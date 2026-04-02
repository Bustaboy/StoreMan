from pydantic import BaseModel, ConfigDict


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_number: str
    description: str
    category: str
    is_serialized: bool
    is_assembly: bool
