from __future__ import annotations
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.dto import (
    QuotePreviewRequest, 
    QuotePreviewResponse, 
    CustomerQuoteFinalizeRequest, 
    CustomerQuoteFinalizeResponse
)
from services.quoting import compute_customer_price, determine_markup_pct
from services.quotes_finalize import finalize_quote as _finalize_service


router = APIRouter(prefix="/quotes", tags=["quotes"])

@router.post("/preview", response_model=QuotePreviewResponse, status_code=200)
def preview_quote(payload: QuotePreviewRequest, db: Session = Depends(get_db)):
    try:
        base_cost = Decimal(str(payload.base_cost))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid base_cost")

    # pick markup
    if payload.markup_override_pct is not None:
        markup_pct = Decimal(str(payload.markup_override_pct))
    else:
        markup_pct = determine_markup_pct(db, category=payload.category, qty=payload.qty)

    total_price = compute_customer_price(base_cost, markup_pct)

    return QuotePreviewResponse(
        category=payload.category,
        qty=payload.qty,
        base_cost=base_cost,
        markup_pct=markup_pct,
        total_price=total_price,
        currency=payload.currency,
    )



@router.post("/finalize", response_model=CustomerQuoteFinalizeResponse, status_code=201)
def finalize_quote(payload: CustomerQuoteFinalizeRequest, db: Session = Depends(get_db)):
    try:
        row = _finalize_service(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CustomerQuoteFinalizeResponse(
        id=row.id,
        project_id=row.project_id,
        selected_supplier_quote_id=row.selected_supplier_quote_id,
        markup_schema_id=row.markup_schema_id,
        subtotal=row.subtotal,
        fees=row.fees,
        tax=row.tax,
        total=row.total,
        status=row.status,
    )