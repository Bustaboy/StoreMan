from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class WorkOrderStatus(str, Enum):
    PENDING = 'Pending'
    IN_PROGRESS = 'In Progress'
    ON_HOLD = 'On Hold'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'


class TransactionType(str, Enum):
    RECEIVE = 'RECEIVE'
    ISSUE = 'ISSUE'
    MOVE = 'MOVE'
    RESERVE = 'RESERVE'
    RETURN = 'RETURN'
    SCRAP = 'SCRAP'
    MAINTENANCE = 'MAINTENANCE'
    PACK_HU = 'PACK_HU'
    PUTAWAY = 'PUTAWAY'
    ASSEMBLE = 'ASSEMBLE'
    DISASSEMBLE = 'DISASSEMBLE'


class Location(Base):
    __tablename__ = 'locations'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default='true')

    materials_defaulting_here: Mapped[list[Material]] = relationship(back_populates='default_location')
    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates='location')
    handling_units: Mapped[list[HandlingUnit]] = relationship(back_populates='location')
    putaway_lines_proposed: Mapped[list[PutawayLine]] = relationship(
        back_populates='proposed_location', foreign_keys='PutawayLine.proposed_location_id'
    )
    putaway_lines_adjusted: Mapped[list[PutawayLine]] = relationship(
        back_populates='adjusted_location', foreign_keys='PutawayLine.adjusted_location_id'
    )
    transactions_from: Mapped[list[Transaction]] = relationship(
        back_populates='from_location', foreign_keys='Transaction.from_location_id'
    )
    transactions_to: Mapped[list[Transaction]] = relationship(
        back_populates='to_location', foreign_keys='Transaction.to_location_id'
    )


class Material(Base):
    __tablename__ = 'materials'

    material_number: Mapped[str] = mapped_column(String(100), primary_key=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    is_serialized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    is_assembly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    max_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    safety_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    default_location_id: Mapped[int | None] = mapped_column(ForeignKey('locations.id'), nullable=True)
    is_dangerous_good: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    dg_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dg_un_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dg_proper_shipping_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dg_segregation_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    sap_material_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    default_location: Mapped[Location | None] = relationship(back_populates='materials_defaulting_here')
    inventory_items: Mapped[list[InventoryItem]] = relationship(back_populates='material')
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates='material')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='material')
    assemblies: Mapped[list[Assembly]] = relationship(back_populates='material')
    component_usages: Mapped[list[AssemblyComponent]] = relationship(back_populates='component_material')


class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[str] = mapped_column(ForeignKey('materials.material_number'), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey('locations.id'), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    revision: Mapped[str | None] = mapped_column(String(100), nullable=True)
    project_specific_bom_notes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_assembly_instance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')

    material: Mapped[Material] = relationship(back_populates='inventory_items')
    location: Mapped[Location] = relationship(back_populates='inventory_items')
    handling_unit_links: Mapped[list[HandlingUnitItem]] = relationship(back_populates='inventory_item')
    reservation_links: Mapped[list[ReservationLink]] = relationship(back_populates='inventory_item')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='inventory_item')
    putaway_lines: Mapped[list[PutawayLine]] = relationship(back_populates='inventory_item')
    maintenance_records: Mapped[list[MaintenanceRecord]] = relationship(back_populates='inventory_item')
    produced_assemblies: Mapped[list[Assembly]] = relationship(back_populates='inventory_item')
    component_usages: Mapped[list[AssemblyComponent]] = relationship(back_populates='component_inventory_item')


class HandlingUnit(Base):
    __tablename__ = 'handling_units'

    id: Mapped[int] = mapped_column(primary_key=True)
    package_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    package_type: Mapped[str] = mapped_column(String(100), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey('locations.id'), nullable=False)
    parent_hu_id: Mapped[int | None] = mapped_column(ForeignKey('handling_units.id'), nullable=True)
    is_bonded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')

    location: Mapped[Location] = relationship(back_populates='handling_units')
    parent_hu: Mapped[HandlingUnit | None] = relationship(back_populates='child_hus', remote_side='HandlingUnit.id')
    child_hus: Mapped[list[HandlingUnit]] = relationship(back_populates='parent_hu')
    items: Mapped[list[HandlingUnitItem]] = relationship(back_populates='handling_unit')
    transactions: Mapped[list[Transaction]] = relationship(back_populates='handling_unit')


class HandlingUnitItem(Base):
    __tablename__ = 'handling_unit_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    handling_unit_id: Mapped[int] = mapped_column(ForeignKey('handling_units.id'), nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey('inventory_items.id'), nullable=False)
    quantity_in_hu: Mapped[int] = mapped_column(Integer, nullable=False)

    handling_unit: Mapped[HandlingUnit] = relationship(back_populates='items')
    inventory_item: Mapped[InventoryItem] = relationship(back_populates='handling_unit_links')


class ProjectReservation(Base):
    __tablename__ = 'project_reservations'

    id: Mapped[int] = mapped_column(primary_key=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vessel: Mapped[str] = mapped_column(String(255), nullable=False)
    load_close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mat_close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_demobilization_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_return_at_boys: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False)

    reservation_links: Mapped[list[ReservationLink]] = relationship(back_populates='project_reservation')
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates='project_reservation')


class ReservationLink(Base):
    __tablename__ = 'reservation_links'

    id: Mapped[int] = mapped_column(primary_key=True)
    project_reservation_id: Mapped[int] = mapped_column(ForeignKey('project_reservations.id'), nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey('inventory_items.id'), nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_hard_reservation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    reserved_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project_reservation: Mapped[ProjectReservation] = relationship(back_populates='reservation_links')
    inventory_item: Mapped[InventoryItem] = relationship(back_populates='reservation_links')


class WorkOrder(Base):
    __tablename__ = 'work_orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    work_order_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    material_id: Mapped[str] = mapped_column(ForeignKey('materials.material_number'), nullable=False)
    project_reservation_id: Mapped[int | None] = mapped_column(ForeignKey('project_reservations.id'), nullable=True)
    quantity_to_build: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_technician: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[WorkOrderStatus] = mapped_column(
        SqlEnum(WorkOrderStatus, name='work_order_status'), nullable=False, default=WorkOrderStatus.PENDING
    )
    on_hold_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    material: Mapped[Material] = relationship(back_populates='work_orders')
    project_reservation: Mapped[ProjectReservation | None] = relationship(back_populates='work_orders')
    maintenance_records: Mapped[list[MaintenanceRecord]] = relationship(back_populates='work_order')
    assemblies: Mapped[list[Assembly]] = relationship(back_populates='work_order')


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    type: Mapped[TransactionType] = mapped_column(SqlEnum(TransactionType, name='transaction_type'), nullable=False)
    material_id: Mapped[str] = mapped_column(ForeignKey('materials.material_number'), nullable=False)
    inventory_item_id: Mapped[int | None] = mapped_column(ForeignKey('inventory_items.id'), nullable=True)
    from_location_id: Mapped[int | None] = mapped_column(ForeignKey('locations.id'), nullable=True)
    to_location_id: Mapped[int | None] = mapped_column(ForeignKey('locations.id'), nullable=True)
    handling_unit_id: Mapped[int | None] = mapped_column(ForeignKey('handling_units.id'), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    user: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    material: Mapped[Material] = relationship(back_populates='transactions')
    inventory_item: Mapped[InventoryItem | None] = relationship(back_populates='transactions')
    from_location: Mapped[Location | None] = relationship(back_populates='transactions_from', foreign_keys=[from_location_id])
    to_location: Mapped[Location | None] = relationship(back_populates='transactions_to', foreign_keys=[to_location_id])
    handling_unit: Mapped[HandlingUnit | None] = relationship(back_populates='transactions')


class Receipt(Base):
    __tablename__ = 'receipts'

    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    receipt_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sap_po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    received_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    putaway_lines: Mapped[list[PutawayLine]] = relationship(back_populates='receipt')


class PutawayLine(Base):
    __tablename__ = 'putaway_lines'

    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey('receipts.id'), nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey('inventory_items.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    proposed_location_id: Mapped[int | None] = mapped_column(ForeignKey('locations.id'), nullable=True)
    adjusted_location_id: Mapped[int | None] = mapped_column(ForeignKey('locations.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default='Pending')
    putaway_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    putaway_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    receipt: Mapped[Receipt] = relationship(back_populates='putaway_lines')
    inventory_item: Mapped[InventoryItem] = relationship(back_populates='putaway_lines')
    proposed_location: Mapped[Location | None] = relationship(
        back_populates='putaway_lines_proposed', foreign_keys=[proposed_location_id]
    )
    adjusted_location: Mapped[Location | None] = relationship(
        back_populates='putaway_lines_adjusted', foreign_keys=[adjusted_location_id]
    )


class MaintenanceRecord(Base):
    __tablename__ = 'maintenance_records'

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey('inventory_items.id'), nullable=False)
    work_order_id: Mapped[int | None] = mapped_column(ForeignKey('work_orders.id'), nullable=True)
    maintenance_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    next_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default='Completed')

    inventory_item: Mapped[InventoryItem] = relationship(back_populates='maintenance_records')
    work_order: Mapped[WorkOrder | None] = relationship(back_populates='maintenance_records')


class Assembly(Base):
    __tablename__ = 'assemblies'

    id: Mapped[int] = mapped_column(primary_key=True)
    work_order_id: Mapped[int | None] = mapped_column(ForeignKey('work_orders.id'), nullable=True)
    inventory_item_id: Mapped[int | None] = mapped_column(ForeignKey('inventory_items.id'), nullable=True)
    material_id: Mapped[str] = mapped_column(ForeignKey('materials.material_number'), nullable=False)
    quantity_built: Mapped[int] = mapped_column(Integer, nullable=False)
    assembled_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assembled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    work_order: Mapped[WorkOrder | None] = relationship(back_populates='assemblies')
    inventory_item: Mapped[InventoryItem | None] = relationship(back_populates='produced_assemblies')
    material: Mapped[Material] = relationship(back_populates='assemblies')
    components: Mapped[list[AssemblyComponent]] = relationship(back_populates='assembly')


class AssemblyComponent(Base):
    __tablename__ = 'assembly_components'

    id: Mapped[int] = mapped_column(primary_key=True)
    assembly_id: Mapped[int] = mapped_column(ForeignKey('assemblies.id'), nullable=False)
    component_material_id: Mapped[str] = mapped_column(ForeignKey('materials.material_number'), nullable=False)
    component_inventory_item_id: Mapped[int | None] = mapped_column(ForeignKey('inventory_items.id'), nullable=True)
    quantity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_consumed: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assembly: Mapped[Assembly] = relationship(back_populates='components')
    component_material: Mapped[Material] = relationship(back_populates='component_usages')
    component_inventory_item: Mapped[InventoryItem | None] = relationship(back_populates='component_usages')
