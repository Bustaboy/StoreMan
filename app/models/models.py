from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TransactionType(str, PyEnum):
    RECEIVE = 'RECEIVE'
    ISSUE = 'ISSUE'
    TRANSFER = 'TRANSFER'
    ADJUST = 'ADJUST'
    ASSEMBLE = 'ASSEMBLE'
    DISASSEMBLE = 'DISASSEMBLE'
    PACK_HU = 'PACK_HU'
    PUTAWAY = 'PUTAWAY'


class WorkOrderStatus(str, PyEnum):
    DRAFT = 'DRAFT'
    RELEASED = 'RELEASED'
    IN_PROGRESS = 'IN_PROGRESS'
    ON_HOLD = 'ON_HOLD'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'


class Location(Base):
    __tablename__ = 'locations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    parent_location: Mapped[Optional['Location']] = relationship(
        'Location', remote_side=[id], back_populates='child_locations'
    )
    child_locations: Mapped[List['Location']] = relationship('Location', back_populates='parent_location')

    materials_with_default: Mapped[List['Material']] = relationship('Material', back_populates='default_location')
    inventory_items: Mapped[List['InventoryItem']] = relationship('InventoryItem', back_populates='location')
    handling_units: Mapped[List['HandlingUnit']] = relationship('HandlingUnit', back_populates='current_location')
    putaway_lines: Mapped[List['PutawayLine']] = relationship('PutawayLine', back_populates='to_location')


class Material(Base):
    __tablename__ = 'materials'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_assembly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_stock: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    max_stock: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    safety_stock: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    default_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'))

    dg_class: Mapped[Optional[str]] = mapped_column(String(32))
    dg_un_number: Mapped[Optional[str]] = mapped_column(String(32))
    dg_packing_group: Mapped[Optional[str]] = mapped_column(String(16))
    dg_transport_category: Mapped[Optional[str]] = mapped_column(String(32))

    sap_material_number: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    default_location: Mapped[Optional[Location]] = relationship('Location', back_populates='materials_with_default')
    inventory_items: Mapped[List['InventoryItem']] = relationship('InventoryItem', back_populates='material')
    reservation_links: Mapped[List['ReservationLink']] = relationship('ReservationLink', back_populates='material')
    work_orders: Mapped[List['WorkOrder']] = relationship('WorkOrder', back_populates='material')
    transactions: Mapped[List['Transaction']] = relationship('Transaction', back_populates='material')
    putaway_lines: Mapped[List['PutawayLine']] = relationship('PutawayLine', back_populates='material')

    assemblies: Mapped[List['Assembly']] = relationship('Assembly', back_populates='material')
    assembly_components: Mapped[List['AssemblyComponent']] = relationship(
        'AssemblyComponent', back_populates='component_material'
    )


class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), index=True)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'), index=True)

    serial_number: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=1, nullable=False)
    revision: Mapped[Optional[str]] = mapped_column(String(64))
    project_specific_bom_notes: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_assembly_instance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    material: Mapped[Material] = relationship('Material', back_populates='inventory_items')
    location: Mapped[Optional[Location]] = relationship('Location', back_populates='inventory_items')

    handling_unit_links: Mapped[List['HandlingUnitItem']] = relationship('HandlingUnitItem', back_populates='inventory_item')
    reservation_links: Mapped[List['ReservationLink']] = relationship('ReservationLink', back_populates='inventory_item')
    maintenance_records: Mapped[List['MaintenanceRecord']] = relationship('MaintenanceRecord', back_populates='inventory_item')
    transactions: Mapped[List['Transaction']] = relationship('Transaction', back_populates='inventory_item')
    putaway_lines: Mapped[List['PutawayLine']] = relationship('PutawayLine', back_populates='inventory_item')


class HandlingUnit(Base):
    __tablename__ = 'handling_units'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hu_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    package_number: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    package_type: Mapped[Optional[str]] = mapped_column(String(64))
    is_bonded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    parent_hu_id: Mapped[Optional[int]] = mapped_column(ForeignKey('handling_units.id', ondelete='SET NULL'), index=True)
    current_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    parent_hu: Mapped[Optional['HandlingUnit']] = relationship(
        'HandlingUnit', remote_side=[id], back_populates='child_hus'
    )
    child_hus: Mapped[List['HandlingUnit']] = relationship('HandlingUnit', back_populates='parent_hu')
    current_location: Mapped[Optional[Location]] = relationship('Location', back_populates='handling_units')

    item_links: Mapped[List['HandlingUnitItem']] = relationship('HandlingUnitItem', back_populates='handling_unit')
    transactions: Mapped[List['Transaction']] = relationship('Transaction', back_populates='handling_unit')


class HandlingUnitItem(Base):
    __tablename__ = 'handling_unit_items'

    handling_unit_id: Mapped[int] = mapped_column(
        ForeignKey('handling_units.id', ondelete='CASCADE'), primary_key=True
    )
    inventory_item_id: Mapped[int] = mapped_column(
        ForeignKey('inventory_items.id', ondelete='CASCADE'), primary_key=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=1, nullable=False)

    handling_unit: Mapped[HandlingUnit] = relationship('HandlingUnit', back_populates='item_links')
    inventory_item: Mapped[InventoryItem] = relationship('InventoryItem', back_populates='handling_unit_links')


class ProjectReservation(Base):
    __tablename__ = 'project_reservations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reservation_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    project_code: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    load_close: Mapped[Optional[date]] = mapped_column(Date)
    mat_close: Mapped[Optional[date]] = mapped_column(Date)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    expected_end_date: Mapped[Optional[date]] = mapped_column(Date)
    expected_demobilization_date: Mapped[Optional[date]] = mapped_column(Date)
    expected_return_at_boys: Mapped[Optional[date]] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    reservation_links: Mapped[List['ReservationLink']] = relationship(
        'ReservationLink', back_populates='project_reservation'
    )


class ReservationLink(Base):
    __tablename__ = 'reservation_links'
    __table_args__ = (
        UniqueConstraint('project_reservation_id', 'inventory_item_id', name='uq_reservation_inventory_item'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_reservation_id: Mapped[int] = mapped_column(
        ForeignKey('project_reservations.id', ondelete='CASCADE'), index=True
    )
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), index=True)
    inventory_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey('inventory_items.id', ondelete='SET NULL'), index=True)

    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    is_hard_reservation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project_reservation: Mapped[ProjectReservation] = relationship(
        'ProjectReservation', back_populates='reservation_links'
    )
    material: Mapped[Material] = relationship('Material', back_populates='reservation_links')
    inventory_item: Mapped[Optional[InventoryItem]] = relationship('InventoryItem', back_populates='reservation_links')


class WorkOrder(Base):
    __tablename__ = 'work_orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), index=True)

    quantity_to_build: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    assigned_technician: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[WorkOrderStatus] = mapped_column(
        SAEnum(WorkOrderStatus, name='work_order_status'), default=WorkOrderStatus.DRAFT, nullable=False
    )
    on_hold_reason: Mapped[Optional[str]] = mapped_column(Text)

    planned_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    planned_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    material: Mapped[Material] = relationship('Material', back_populates='work_orders')
    transactions: Mapped[List['Transaction']] = relationship('Transaction', back_populates='work_order')
    receipts: Mapped[List['Receipt']] = relationship('Receipt', back_populates='work_order')


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name='transaction_type'), nullable=False, index=True
    )

    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), index=True)
    inventory_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey('inventory_items.id', ondelete='SET NULL'), index=True)
    handling_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey('handling_units.id', ondelete='SET NULL'), index=True)
    work_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey('work_orders.id', ondelete='SET NULL'), index=True)

    from_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'))
    to_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'))

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    performed_by: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    material: Mapped[Material] = relationship('Material', back_populates='transactions')
    inventory_item: Mapped[Optional[InventoryItem]] = relationship('InventoryItem', back_populates='transactions')
    handling_unit: Mapped[Optional[HandlingUnit]] = relationship('HandlingUnit', back_populates='transactions')
    work_order: Mapped[Optional[WorkOrder]] = relationship('WorkOrder', back_populates='transactions')


class Receipt(Base):
    __tablename__ = 'receipts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    work_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey('work_orders.id', ondelete='SET NULL'), index=True)

    supplier_name: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    received_by: Mapped[Optional[str]] = mapped_column(String(255))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    work_order: Mapped[Optional[WorkOrder]] = relationship('WorkOrder', back_populates='receipts')
    putaway_lines: Mapped[List['PutawayLine']] = relationship('PutawayLine', back_populates='receipt')


class PutawayLine(Base):
    __tablename__ = 'putaway_lines'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey('receipts.id', ondelete='CASCADE'), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), index=True)
    inventory_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey('inventory_items.id', ondelete='SET NULL'), index=True)
    to_location_id: Mapped[int] = mapped_column(ForeignKey('locations.id', ondelete='RESTRICT'), index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    putaway_by: Mapped[Optional[str]] = mapped_column(String(255))
    putaway_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    receipt: Mapped[Receipt] = relationship('Receipt', back_populates='putaway_lines')
    material: Mapped[Material] = relationship('Material', back_populates='putaway_lines')
    inventory_item: Mapped[Optional[InventoryItem]] = relationship('InventoryItem', back_populates='putaway_lines')
    to_location: Mapped[Location] = relationship('Location', back_populates='putaway_lines')


class MaintenanceRecord(Base):
    __tablename__ = 'maintenance_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey('inventory_items.id', ondelete='CASCADE'), index=True)

    maintenance_type: Mapped[str] = mapped_column(String(128), index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    performed_by: Mapped[Optional[str]] = mapped_column(String(255))
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    next_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    inventory_item: Mapped[InventoryItem] = relationship('InventoryItem', back_populates='maintenance_records')


class Assembly(Base):
    __tablename__ = 'assemblies'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='CASCADE'), index=True)
    revision: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    material: Mapped[Material] = relationship('Material', back_populates='assemblies')
    components: Mapped[List['AssemblyComponent']] = relationship('AssemblyComponent', back_populates='assembly')


class AssemblyComponent(Base):
    __tablename__ = 'assembly_components'
    __table_args__ = (
        UniqueConstraint('assembly_id', 'component_material_id', name='uq_assembly_component_material'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assembly_id: Mapped[int] = mapped_column(ForeignKey('assemblies.id', ondelete='CASCADE'), index=True)
    component_material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), index=True)

    required_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bom_notes: Mapped[Optional[str]] = mapped_column(Text)

    assembly: Mapped[Assembly] = relationship('Assembly', back_populates='components')
    component_material: Mapped[Material] = relationship('Material', back_populates='assembly_components')
