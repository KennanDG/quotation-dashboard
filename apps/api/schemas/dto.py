from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Annotated, List, Optional

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

class UserUpdate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: Optional[Literal["PM", "SOURCING", "LEADERSHIP", "ADMIN"]] = None



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

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    service_type: Optional[str] = None  # design|pcba|im|prototyping
    status: Optional[str] = None
    owner_id: Optional[int] = None
    intake: Optional[dict] = None
    calc_snapshot: Optional[dict] = None
    


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

class RFQUpdate(BaseModel):
    project_id: Optional[int] = None
    created_by: Optional[int] = None
    assigned_to: Optional[int] = None
    requirements: Optional[dict] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None




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

class SupplierQuoteUpdate(BaseModel):
    rfq_id: Optional[int] = None
    supplier_name: Optional[str] = None
    currency: Optional[str] = None
    tooling_cost: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    moq: Optional[int] = None
    lead_time_days: Optional[int] = None
    notes: Optional[str] = None
    raw: Optional[dict] = None
    status: Optional[str] = None




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

class MarkupSchemaUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    rules: dict[str, MarkupRulesForService] | None = None




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

class CustomerQuoteUpdate(BaseModel):
    # identifiers
    selected_supplier_quote_id: Optional[int] = None
    markup_schema_id: Optional[int] = None

    # pricing + content
    line_items: Optional[dict] = None
    subtotal: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    valid_until: Optional[date] = None
    status: Optional[str] = None
    snapshot: Optional[dict] = None

    # human-facing id
    quote_number: Optional[str] = None




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

class ApprovalUpdate(BaseModel):
    object_type: Optional[Literal["supplier_quote", "customer_quote"]] = None
    approver_id: Optional[int] = None
    decision: Optional[Literal["approved", "rejected"]] = None
    reason: Optional[str] = None




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




# ---------- Quote Finalize ----------

class LineItem(BaseModel):
    description: str
    qty: Annotated[int, Field(strict=True, ge=1)]
    unit_cost: Decimal  # pre-markup cost per unit

class CustomerQuoteFinalizeRequest(BaseModel):
    project_id: int
    selected_supplier_quote_id: int | None = None

    # Either provide detailed items OR a simple base_cost/qty
    line_items: list[LineItem] | None = None
    base_cost: Decimal | None = None
    qty: Annotated[int, Field(strict=True, ge=1)] | None = None
    category: str | None = None  # e.g., "im"

    markup_schema_id: int | None = None
    markup_override_pct: Decimal | None = None

    fees: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    valid_until: date | None = None
    status: str = "draft"

class CustomerQuoteFinalizeResponse(BaseModel):
    id: int
    project_id: int
    selected_supplier_quote_id: int | None
    markup_schema_id: int
    subtotal: Decimal
    fees: Decimal
    tax: Decimal
    total: Decimal
    status: str
