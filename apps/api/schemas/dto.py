from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Annotated

from pydantic import BaseModel, Field, EmailStr, conint, confloat
from typing_extensions import Literal



# ---------- Users ----------

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    role: Literal["PM", "SOURCING", "LEADERSHIP", "ADMIN"] = "PM"

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    created_at: datetime
    class Config:
        from_attributes = True



# ---------- Projects ----------

class ProjectCreate(BaseModel):
    name: str
    client_name: str | None = None
    service_type: Literal["design", "pcba", "im", "prototyping"]
    status: str = "draft"
    owner_id: int | None = None
    intake: dict | None = None
    calc_snapshot: dict | None = None

class ProjectRead(BaseModel):
    id: int
    name: str
    client_name: str | None
    service_type: str
    status: str
    owner_id: int | None
    intake: dict | None
    calc_snapshot: dict | None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
    


# ---------- RFQs ----------

class RFQCreate(BaseModel):
    project_id: int
    created_by: int
    assigned_to: int | None = None
    requirements: dict | None = None
    status: str = "draft"
    due_date: datetime | None = None

class RFQRead(BaseModel):
    id: int
    project_id: int
    created_by: int
    assigned_to: int | None
    requirements: dict | None
    status: str
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True




# ---------- Supplier Quotes ----------

class SupplierQuoteCreate(BaseModel):
    rfq_id: int
    supplier_name: str
    currency: str = "USD"
    tooling_cost: Decimal | None = Field(default=None)
    unit_price: Decimal | None = Field(default=None)
    moq: Annotated[int, Field(strict=True, ge=1)] | None = None
    lead_time_days: Annotated[int, Field(strict=True, ge=1)] | None = None
    notes: str | None = None
    raw: dict | None = None
    status: str = "received"

class SupplierQuoteRead(BaseModel):
    id: int
    rfq_id: int
    supplier_name: str
    currency: str
    tooling_cost: Decimal | None
    unit_price: Decimal | None
    moq: int | None
    lead_time_days: int | None
    notes: str | None
    raw: dict | None
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True




# ---------- Markup Schema ----------

class MarkupRuleBand(BaseModel):
    min_qty: int
    max_qty: int | None = None
    markup_percent: Decimal

class MarkupRulesForService(BaseModel):
    bands: list[MarkupRuleBand]

class MarkupSchemaCreate(BaseModel):
    name: str
    is_active: bool = True
    rules: dict[str, MarkupRulesForService] # rules keyed by service_type (design|pcba|im|prototyping)

class MarkupSchemaRead(MarkupSchemaCreate):
    id: int
    name: str
    rules: dict | None = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True




# ---------- Customer Quote (future finalize workflow) ----------
class CustomerQuoteCreate(BaseModel):
    project_id: int
    selected_supplier_quote_id: int | None = None
    markup_schema_id: int
    line_items: dict = Field(default_factory=dict)
    subtotal: Decimal
    fees: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    total: Decimal
    valid_until: date | None = None
    status: str = "draft"
    snapshot: dict | None = None

class CustomerQuoteRead(CustomerQuoteCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True




# ---------- Approval ----------

class ApprovalCreate(BaseModel):
    object_type: Literal["supplier_quote", "customer_quote"]
    object_id: int
    approver_id: int
    decision: Literal["approved", "rejected"]
    reason: str | None = None

class ApprovalRead(ApprovalCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True




# ---------- Quote Preview ----------

class QuotePreviewRequest(BaseModel):
    category: str = Field(..., examples=["im"])  # maps to a key inside MarkupSchema.rules
    qty: Annotated[int, Field(strict=True, ge=1)] = Field(..., examples=[250])
    base_cost: Decimal = Field(..., examples=["1234.56"])
    markup_override_pct: Decimal | None = None
    currency: str = "USD"

class QuotePreviewResponse(BaseModel):
    category: str
    qty: int
    base_cost: Decimal
    markup_pct: Decimal
    total_price: Decimal
    currency: str = "USD"