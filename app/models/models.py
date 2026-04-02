from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Material(Base):
    __tablename__ = "materials"

    material_number: Mapped[str] = mapped_column(String(100), primary_key=True, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False)
    is_assembly: Mapped[bool] = mapped_column(Boolean, default=False)
    min_stock: Mapped[int | None] = mapped_column(Integer)
    max_stock: Mapped[int | None] = mapped_column(Integer)
    safety_stock: Mapped[int | None] = mapped_column(Integer)
    default_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    is_dangerous_good: Mapped[bool] = mapped_column(Boolean, default=False)
    dg_class: Mapped[str | None] = mapped_column(String, nullable=True)
    dg_un_number: Mapped[str | None] = mapped_column(String, nullable=True)
    dg_proper_shipping_name: Mapped[str | None] = mapped_column(String, nullable=True)
    dg_segregation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sap_material_number: Mapped[str | None] = mapped_column(String, nullable=True)

    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates="material")
    default_location: Mapped[Location | None] = relationship(
        back_populates="default_for_materials",
        foreign_keys=[default_location_id],
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[str] = mapped_column(String(100), ForeignKey("materials.material_number"))
    serial_number: Mapped[str | None] = mapped_column(String, nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    status: Mapped[str] = mapped_column(String, default="IN_STOCK")
    revision: Mapped[str | None] = mapped_column(String, nullable=True)
    project_specific_bom_notes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_assembly_instance: Mapped[bool] = mapped_column(Boolean, default=False)

    material: Mapped[Material] = relationship(back_populates="inventory_items")
    location: Mapped[Location] = relationship(back_populates="inventory_items")
    handling_unit_items: Mapped[list[HandlingUnitItem]] = relationship(back_populates="inventory_item")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates="location")
    handling_units: Mapped[list[HandlingUnit]] = relationship(back_populates="location")
    default_for_materials: Mapped[list[Material]] = relationship(
        back_populates="default_location",
        foreign_keys=[Material.default_location_id],
    )


class HandlingUnit(Base):
    __tablename__ = "handling_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_number: Mapped[str] = mapped_column(String(100), unique=True)
    package_type: Mapped[str] = mapped_column(String(100))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    parent_hu_id: Mapped[int | None] = mapped_column(ForeignKey("handling_units.id"), nullable=True)
    is_bonded: Mapped[bool] = mapped_column(Boolean, default=False)

    location: Mapped[Location] = relationship(back_populates="handling_units")
    parent_hu: Mapped[HandlingUnit | None] = relationship(
        back_populates="child_hus",
        remote_side=[id],
    )
    child_hus: Mapped[list[HandlingUnit]] = relationship(back_populates="parent_hu")
    handling_unit_items: Mapped[list[HandlingUnitItem]] = relationship(back_populates="handling_unit")


class HandlingUnitItem(Base):
    __tablename__ = "handling_unit_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    handling_unit_id: Mapped[int] = mapped_column(ForeignKey("handling_units.id"))
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    quantity_in_hu: Mapped[int] = mapped_column(Integer, default=1)

    handling_unit: Mapped[HandlingUnit] = relationship(back_populates="handling_unit_items")
    inventory_item: Mapped[InventoryItem] = relationship(back_populates="handling_unit_items")
