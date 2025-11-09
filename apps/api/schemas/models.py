from __future__ import annotations
from datetime import datetime, date
import enum
from sqlalchemy import (
    String, Text, Integer, DateTime, Date, Boolean, ForeignKey, Enum, Numeric
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# --- Enums ------------------------------------------------------------
class Role(str, enum.Enum):
    PM = "PM"
    SOURCING = "SOURCING"
    LEADERSHIP = "LEADERSHIP"
    ADMIN = "ADMIN"

class ServiceType(str, enum.Enum):
    design = "design"
    pcba = "pcba"
    im = "im"
    prototyping = "prototyping"


# --- Tables -----------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, name="role_enum"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    client_name: Mapped[str | None] = mapped_column(String(255))
    service_type: Mapped[ServiceType] = mapped_column(Enum(ServiceType, name="service_enum"))
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    intake: Mapped[dict | None] = mapped_column(JSONB)
    calc_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # cad|bom|supplier_quote|pdf|other
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    storage_url: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RFQ(Base):
    __tablename__ = "rfqs"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    requirements: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)   # draft|sent|collecting|closed
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SupplierQuote(Base):
    __tablename__ = "supplier_quotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    rfq_id: Mapped[int] = mapped_column(ForeignKey("rfqs.id"), index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), index=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    tooling_cost: Mapped[float | None] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 4))
    moq: Mapped[int | None] = mapped_column(Integer)
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="received", index=True)  # received|approved|rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InternalEstimate(Base):
    __tablename__ = "internal_estimates"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    category: Mapped[str] = mapped_column(String(32))  # labor|material|overhead|nre|shipping|tax|misc
    description: Mapped[str | None] = mapped_column(Text)
    qty: Mapped[float] = mapped_column(Numeric(12, 3), default=1)
    rate: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)  # store or compute; MVP store
    meta: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarkupSchema(Base):
    __tablename__ = "markup_schemas"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    rules: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CustomerQuote(Base):
    __tablename__ = "customer_quotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    quote_number: Mapped[str | None] = mapped_column(
        String(32), unique=True, index=True
    )
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    selected_supplier_quote_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_quotes.id"))
    markup_schema_id: Mapped[int] = mapped_column(ForeignKey("markup_schemas.id"))
    line_items: Mapped[dict] = mapped_column(JSONB)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2))
    fees: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    tax: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2))
    valid_until: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)  # draft|approved|sent|accepted|lost
    snapshot: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(32))  # supplier_quote|customer_quote
    object_id: Mapped[int] = mapped_column(Integer)
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(16))  # approved|rejected
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)