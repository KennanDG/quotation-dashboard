from __future__ import annotations
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.dto import QuotePreviewRequest, QuotePreviewResponse
from services.quoting import compute_customer_price, determine_markup_pct



router = APIRouter(prefix="/quotes", tags=["quotes"])

@router.post("/preview", response_model=QuotePreviewResponse)
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