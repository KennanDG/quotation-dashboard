from __future__ import annotations
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from schemas.models import MarkupSchema

DEC2 = Decimal("0.01")


def get_active_markup_schema(db: Session) -> Optional[MarkupSchema]:
    """Return the first active markup schema (or None if missing)."""
    return (
        db.query(MarkupSchema)
        .filter(MarkupSchema.is_active.is_(True))
        .order_by(MarkupSchema.id.asc())
        .first()
    )



def find_markup_percent_from_rules(rules: dict, category: str, qty: int) -> Decimal:
    """
    Search inside the MarkupSchema.rules JSON for the correct band.
    Expected structure:
      {
        "im": {"bands": [{"min_qty": 1, "max_qty": 49, "markup_percent": "35.0"}, ...]},
        "cnc_machining": {...},
        ...
      }
    """
    service = rules.get(category)
    
    if not service:
        return Decimal("0")

    for band in service.get("bands", []):
        min_q = band.get("min_qty", 0)
        max_q = band.get("max_qty", 10**9)
        
        if min_q <= qty <= (max_q or 10**9):
            return Decimal(str(band.get("markup_percent", "0")))
        
    return Decimal("0")



def compute_customer_price(base_cost: Decimal, markup_pct: Decimal) -> Decimal:
    """
    total = base_cost * (1 + markup_pct/100), rounded to cents.
    """
    total = base_cost * (Decimal("1") + (markup_pct / Decimal("100")))
    return total.quantize(DEC2)




def determine_markup_pct(db: Session, *, category: str, qty: int) -> Decimal:
    """
    High-level helper: fetch active schema, pull percent for given category/qty.
    """
    schema = get_active_markup_schema(db)
    if not schema or not schema.rules:
        return Decimal("0")
    
    return find_markup_percent_from_rules(schema.rules, category, qty)