from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Material(TimestampMixin, Base):
    __tablename__ = 'materials'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_assembly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    min_stock: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    max_stock: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0, nullable=False)

    default_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'))

    dg_un_number: Mapped[str | None] = mapped_column(String(20))
    dg_hazard_class: Mapped[str | None] = mapped_column(String(20))
    dg_packing_group: Mapped[str | None] = mapped_column(String(20))
    dg_metadata: Mapped[dict | None] = mapped_column(JSONB)

    default_location: Mapped[Location | None] = relationship(back_populates='defaulted_materials')
    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates='material')
    project_reservations: Mapped[list[ProjectReservation]] = relationship(back_populates='material')
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates='material')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='material')
    assemblies: Mapped[list[Assembly]] = relationship(back_populates='material')
    assembly_components: Mapped[list[AssemblyComponent]] = relationship(back_populates='component_material')

    __table_args__ = (
        CheckConstraint('min_stock >= 0', name='ck_material_min_stock_non_negative'),
        CheckConstraint('safety_stock >= 0', name='ck_material_safety_stock_non_negative'),
    )


class Location(TimestampMixin, Base):
    __tablename__ = 'locations'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location_type: Mapped[str] = mapped_column(String(50), default='storage', nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    defaulted_materials: Mapped[list[Material]] = relationship(back_populates='default_location')
    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates='location', foreign_keys='InventoryItem.location_id')
    handling_units: Mapped[list[HandlingUnit]] = relationship(back_populates='current_location')
    putaway_from_lines: Mapped[list[PutawayLine]] = relationship(
        back_populates='from_location', foreign_keys='PutawayLine.from_location_id'
    )
    putaway_to_lines: Mapped[list[PutawayLine]] = relationship(
        back_populates='to_location', foreign_keys='PutawayLine.to_location_id'
    )
    outgoing_transactions: Mapped[list[Transaction]] = relationship(
        back_populates='from_location', foreign_keys='Transaction.from_location_id'
    )
    incoming_transactions: Mapped[list[Transaction]] = relationship(
        back_populates='to_location', foreign_keys='Transaction.to_location_id'
    )


class InventoryItem(TimestampMixin, Base):
    __tablename__ = 'inventory_items'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), nullable=False, index=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'), index=True)

    serial_number: Mapped[str | None] = mapped_column(String(150), unique=True, index=True)
    batch_number: Mapped[str | None] = mapped_column(String(150), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=1, nullable=False)
    revision: Mapped[str | None] = mapped_column(String(50))
    lot_number: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40), default='available', nullable=False, index=True)

    project_specific_bom_notes: Mapped[dict | None] = mapped_column(JSONB)
    attributes: Mapped[dict | None] = mapped_column(JSONB)

    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    material: Mapped[Material] = relationship(back_populates='inventory_items')
    location: Mapped[Location | None] = relationship(back_populates='inventory_items', foreign_keys=[location_id])
    handling_unit_links: Mapped[list[HandlingUnitItem]] = relationship(back_populates='inventory_item')
    reservation_links: Mapped[list[ReservationLink]] = relationship(back_populates='inventory_item')
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates='inventory_item')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='inventory_item')
    putaway_lines: Mapped[list[PutawayLine]] = relationship(back_populates='inventory_item')
    maintenance_records: Mapped[list[MaintenanceRecord]] = relationship(back_populates='inventory_item')
    component_usages: Mapped[list[AssemblyComponent]] = relationship(back_populates='component_inventory_item')

    __table_args__ = (CheckConstraint('quantity >= 0', name='ck_inventory_item_quantity_non_negative'),)


class HandlingUnit(TimestampMixin, Base):
    __tablename__ = 'handling_units'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hu_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hu_type: Mapped[str] = mapped_column(String(50), default='container', nullable=False)
    status: Mapped[str] = mapped_column(String(40), default='active', nullable=False)

    parent_hu_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('handling_units.id', ondelete='SET NULL'), index=True)
    current_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'), index=True)

    parent_hu: Mapped[HandlingUnit | None] = relationship(back_populates='child_hus', remote_side='HandlingUnit.id')
    child_hus: Mapped[list[HandlingUnit]] = relationship(back_populates='parent_hu')
    current_location: Mapped[Location | None] = relationship(back_populates='handling_units')
    items: Mapped[list[HandlingUnitItem]] = relationship(back_populates='handling_unit')
    reservation_links: Mapped[list[ReservationLink]] = relationship(back_populates='handling_unit')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='handling_unit')


class HandlingUnitItem(TimestampMixin, Base):
    __tablename__ = 'handling_unit_items'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    handling_unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('handling_units.id', ondelete='CASCADE'), nullable=False, index=True
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=1, nullable=False)

    handling_unit: Mapped[HandlingUnit] = relationship(back_populates='items')
    inventory_item: Mapped[InventoryItem] = relationship(back_populates='handling_unit_links')

    __table_args__ = (
        UniqueConstraint('handling_unit_id', 'inventory_item_id', name='uq_handling_unit_item_pair'),
        CheckConstraint('quantity >= 0', name='ck_handling_unit_item_quantity_non_negative'),
    )


class ProjectReservation(TimestampMixin, Base):
    __tablename__ = 'project_reservations'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), nullable=False, index=True)

    requested_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    is_hard_reservation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(String(40), default='open', nullable=False, index=True)
    needed_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    material: Mapped[Material] = relationship(back_populates='project_reservations')
    links: Mapped[list[ReservationLink]] = relationship(back_populates='reservation')
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates='reservation')

    __table_args__ = (
        CheckConstraint('requested_quantity >= 0', name='ck_project_reservation_requested_quantity_non_negative'),
        CheckConstraint('reserved_quantity >= 0', name='ck_project_reservation_reserved_quantity_non_negative'),
    )


class ReservationLink(TimestampMixin, Base):
    __tablename__ = 'reservation_links'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('project_reservations.id', ondelete='CASCADE'), nullable=False, index=True
    )

    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('inventory_items.id', ondelete='CASCADE'), index=True
    )
    handling_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('handling_units.id', ondelete='CASCADE'), index=True)

    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    is_hard_reservation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    reservation: Mapped[ProjectReservation] = relationship(back_populates='links')
    inventory_item: Mapped[InventoryItem | None] = relationship(back_populates='reservation_links')
    handling_unit: Mapped[HandlingUnit | None] = relationship(back_populates='reservation_links')

    __table_args__ = (CheckConstraint('reserved_quantity >= 0', name='ck_reservation_link_reserved_quantity_non_negative'),)


class WorkOrder(TimestampMixin, Base):
    __tablename__ = 'work_orders'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('inventory_items.id', ondelete='SET NULL'), index=True)
    reservation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('project_reservations.id', ondelete='SET NULL'), index=True
    )

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default='open', nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default='normal', nullable=False)
    on_hold_reason: Mapped[str | None] = mapped_column(Text)
    assigned_technician: Mapped[str | None] = mapped_column(String(150), index=True)

    scheduled_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    material: Mapped[Material] = relationship(back_populates='work_orders')
    inventory_item: Mapped[InventoryItem | None] = relationship(back_populates='work_orders')
    reservation: Mapped[ProjectReservation | None] = relationship(back_populates='work_orders')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='work_order')
    maintenance_records: Mapped[list[MaintenanceRecord]] = relationship(back_populates='work_order')
    assemblies: Mapped[list[Assembly]] = relationship(back_populates='work_order')

    __table_args__ = (CheckConstraint('quantity >= 0', name='ck_work_order_quantity_non_negative'),)


class Receipt(TimestampMixin, Base):
    __tablename__ = 'receipts'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    supplier_reference: Mapped[str | None] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(40), default='open', nullable=False, index=True)
    received_by: Mapped[str | None] = mapped_column(String(150))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    transactions: Mapped[list[Transaction]] = relationship(back_populates='receipt')
    putaway_lines: Mapped[list[PutawayLine]] = relationship(back_populates='receipt')


class Transaction(TimestampMixin, Base):
    __tablename__ = 'transactions'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    material_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('materials.id', ondelete='SET NULL'), index=True)
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('inventory_items.id', ondelete='SET NULL'), index=True)
    handling_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('handling_units.id', ondelete='SET NULL'), index=True)
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('work_orders.id', ondelete='SET NULL'), index=True)
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('receipts.id', ondelete='SET NULL'), index=True)

    from_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'), index=True)
    to_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'), index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    transaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(120), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    material: Mapped[Material | None] = relationship(back_populates='transactions')
    inventory_item: Mapped[InventoryItem | None] = relationship(back_populates='transactions')
    handling_unit: Mapped[HandlingUnit | None] = relationship(back_populates='transactions')
    work_order: Mapped[WorkOrder | None] = relationship(back_populates='transactions')
    receipt: Mapped[Receipt | None] = relationship(back_populates='transactions')
    from_location: Mapped[Location | None] = relationship(back_populates='outgoing_transactions', foreign_keys=[from_location_id])
    to_location: Mapped[Location | None] = relationship(back_populates='incoming_transactions', foreign_keys=[to_location_id])


class PutawayLine(TimestampMixin, Base):
    __tablename__ = 'putaway_lines'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('receipts.id', ondelete='CASCADE'), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False, index=True
    )

    from_location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('locations.id', ondelete='SET NULL'), index=True)
    to_location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('locations.id', ondelete='RESTRICT'), nullable=False, index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default='pending', nullable=False, index=True)
    handled_by: Mapped[str | None] = mapped_column(String(150))
    putaway_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    receipt: Mapped[Receipt] = relationship(back_populates='putaway_lines')
    inventory_item: Mapped[InventoryItem] = relationship(back_populates='putaway_lines')
    from_location: Mapped[Location | None] = relationship(back_populates='putaway_from_lines', foreign_keys=[from_location_id])
    to_location: Mapped[Location] = relationship(back_populates='putaway_to_lines', foreign_keys=[to_location_id])

    __table_args__ = (CheckConstraint('quantity >= 0', name='ck_putaway_line_quantity_non_negative'),)


class MaintenanceRecord(TimestampMixin, Base):
    __tablename__ = 'maintenance_records'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False, index=True
    )
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('work_orders.id', ondelete='SET NULL'), index=True)

    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default='completed', nullable=False, index=True)
    performed_by: Mapped[str | None] = mapped_column(String(150))
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    findings: Mapped[dict | None] = mapped_column(JSONB)
    actions_taken: Mapped[dict | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)

    inventory_item: Mapped[InventoryItem] = relationship(back_populates='maintenance_records')
    work_order: Mapped[WorkOrder | None] = relationship(back_populates='maintenance_records')


class Assembly(TimestampMixin, Base):
    __tablename__ = 'assemblies'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('materials.id', ondelete='RESTRICT'), nullable=False, index=True)
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('work_orders.id', ondelete='SET NULL'), index=True)

    assembly_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default='in_progress', nullable=False, index=True)
    bom_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)

    material: Mapped[Material] = relationship(back_populates='assemblies')
    work_order: Mapped[WorkOrder | None] = relationship(back_populates='assemblies')
    components: Mapped[list[AssemblyComponent]] = relationship(back_populates='assembly')


class AssemblyComponent(TimestampMixin, Base):
    __tablename__ = 'assembly_components'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assembly_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('assemblies.id', ondelete='CASCADE'), nullable=False, index=True)

    component_material_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('materials.id', ondelete='RESTRICT'), nullable=False, index=True
    )
    component_inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('inventory_items.id', ondelete='SET NULL'), index=True
    )

    required_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    consumed_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    bom_line_notes: Mapped[dict | None] = mapped_column(JSONB)

    assembly: Mapped[Assembly] = relationship(back_populates='components')
    component_material: Mapped[Material] = relationship(back_populates='assembly_components')
    component_inventory_item: Mapped[InventoryItem | None] = relationship(back_populates='component_usages')

    __table_args__ = (
        CheckConstraint('required_quantity >= 0', name='ck_assembly_component_required_quantity_non_negative'),
        CheckConstraint('consumed_quantity >= 0', name='ck_assembly_component_consumed_quantity_non_negative'),
    )
