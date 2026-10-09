import uuid
from datetime import datetime

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class WorkspaceORM(Base):
    __tablename__ = "workspaces"
    id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, nullable=False)
    floor = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    type = Column(String, nullable=False, default="estacao")
    capacity = Column(Integer, nullable=False, default=1)
    resources = Column(Text, nullable=True)


class AvailabilityWindowORM(Base):
    __tablename__ = "availability_windows"
    workspace_id = Column(SA_UUID(as_uuid=True), ForeignKey("workspaces.id"), primary_key=True)
    day = Column(String, primary_key=True)
    slot_index = Column(Integer, primary_key=True)
    seats = Column(Integer, nullable=False)
    version_id = Column(Integer, nullable=False, default=1)


class BookingORM(Base):
    __tablename__ = "bookings"
    id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(SA_UUID(as_uuid=True), ForeignKey("workspaces.id"))
    employee_id = Column(SA_UUID(as_uuid=True), ForeignKey("employees.id"))
    cost_center_id = Column(SA_UUID(as_uuid=True), ForeignKey("cost_centers.id"))
    slot_start = Column(DateTime, nullable=False)
    slot_end = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow)


class BookingWindowORM(Base):
    __tablename__ = "booking_windows"
    booking_id = Column(SA_UUID(as_uuid=True), ForeignKey("bookings.id"), primary_key=True)
    workspace_id = Column(SA_UUID(as_uuid=True), primary_key=True)
    day = Column(String, primary_key=True)
    slot_index = Column(Integer, primary_key=True)


class QuotaPeriodORM(Base):
    __tablename__ = "quota_periods"
    cost_center_id = Column(SA_UUID(as_uuid=True), ForeignKey("cost_centers.id"), primary_key=True)
    period_start = Column(DateTime, primary_key=True)
    period_end = Column(DateTime, primary_key=True)
    total_hours = Column(Numeric(10, 2), nullable=False)
    consumed_hours = Column(Numeric(10, 2), nullable=False, default=0)


class EmployeeORM(Base):
    __tablename__ = "employees"
    id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=True)
    cost_center_id = Column(SA_UUID(as_uuid=True), ForeignKey("cost_centers.id"))
    is_eligible_for_booking = Column(Boolean, default=False)


class CostCenterORM(Base):
    __tablename__ = "cost_centers"
    id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    monthly_quota_hours = Column(Numeric(10, 2), default=0)


class WaitlistORM(Base):
    __tablename__ = "waitlist"
    id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(SA_UUID(as_uuid=True), ForeignKey("workspaces.id"))
    employee_id = Column(SA_UUID(as_uuid=True), ForeignKey("employees.id"))
    desired_start = Column(DateTime)
    desired_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified_at = Column(DateTime, nullable=True)


class AuditLogORM(Base):
    __tablename__ = "audit_log"
    id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(SA_UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(String, default="")


class HolidayORM(Base):
    __tablename__ = "holidays"
    day = Column(DateTime, primary_key=True)
    description = Column(String, default="")
