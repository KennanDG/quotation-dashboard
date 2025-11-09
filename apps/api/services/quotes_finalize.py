from __future__ import annotations
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from schemas.models import CustomerQuote, MarkupSchema
from schemas.dto import CustomerQuoteFinalizeRequest, LineItem
from services.quoting import determine_markup_pct, compute_customer_price
from services.quote_numbers import next_quote_number


DEC2 = Decimal("0.01")



def _get_active_schema_id(db: Session) -> Optional[int]:
    ''' Retruns the row id of the active markup schema '''
    row = (
        db.query(MarkupSchema)
          .filter(MarkupSchema.is_active.is_(True))
          .order_by(MarkupSchema.id.asc())
          .first()
    )
    return row.id if row else None



def _subtotal_from_items(items: list[LineItem]) -> Decimal:
    ''' Base cost before markup '''
    s = Decimal("0")
    for li in items:
        s += Decimal(str(li.unit_cost)) * Decimal(int(li.qty))
    return s.quantize(DEC2)



def _resolve_markup_pct(
        db: Session, 
        payload: CustomerQuoteFinalizeRequest, 
        computed_qty: int | None
        ) -> Decimal:
    '''
    Determines appropriate markup based on the project category & qty
    frontend can override markup percentage if it is included in the payload
    '''
    if payload.markup_override_pct is not None:
        return Decimal(str(payload.markup_override_pct))
    
    category = payload.category or "im"
    qty = computed_qty or payload.qty or 1

    return determine_markup_pct(db, category=category, qty=int(qty))



def finalize_quote(db: Session, payload: CustomerQuoteFinalizeRequest) -> CustomerQuote:
    '''
    Finalizes a customer quote by computing totals, applying markup rules, and persisting
    a `CustomerQuote` record with a full calculation snapshot.

    This function supports two input modes:
      1. **Line item mode** — where individual cost items (`line_items`) are provided.
      2. **Simple mode** — where a single `base_cost`, `qty`, and `category` are provided.

    Based on the active or provided `MarkupSchema`, it determines the appropriate markup
    percentage for the given category and quantity, computes the subtotal, applies markup,
    then adds any fees and tax to produce a final total. The resulting quote record includes
    a `snapshot` of all inputs and computed values for auditability and reproducibility.

    Args:
        db (Session):
            SQLAlchemy database session used for reading markup schemas and persisting
            the new `CustomerQuote` record.
        payload (CustomerQuoteFinalizeRequest):
            Validated request data containing project references, costs, markup overrides,
            optional supplier quote linkage, and fee/tax values.

    Raises:
        ValueError: If no active markup schema exists, or if neither `line_items` nor both
            `base_cost` and `qty` are provided.

    Returns:
        CustomerQuote:
            The newly created and committed `CustomerQuote` SQLAlchemy object representing
            the finalized quote, including all computed totals and a complete calculation
            snapshot.

    Example:
        >>> finalize_quote(db, CustomerQuoteFinalizeRequest(
        ...     project_id=1,
        ...     base_cost=Decimal("1234.56"),
        ...     qty=250,
        ...     category="im",
        ...     fees=Decimal("25.00"),
        ...     tax=Decimal("0.00"),
        ... ))
        <CustomerQuote id=42 project_id=1 total=1505.56>
    '''
    schema_id = payload.markup_schema_id or _get_active_schema_id(db)
    if not schema_id:
        raise ValueError("No active markup schema found and none provided.")

    # 2) subtotal & qty
    if payload.line_items:
        subtotal = _subtotal_from_items(payload.line_items)
        computed_qty = sum(int(li.qty) for li in payload.line_items)
        line_items_json = {
            "mode": "items",
            "items": [li.model_dump(mode="json") for li in payload.line_items]
        }
    else:
        if payload.base_cost is None or payload.qty is None:
            raise ValueError("Provide either line_items or (base_cost and qty).")
        
        subtotal = Decimal(str(payload.base_cost)).quantize(DEC2)
        computed_qty = int(payload.qty)

        # Store a simple single line so the snapshot/line_items is never empty
        per_unit = (subtotal / Decimal(computed_qty)).quantize(DEC2)
        line_items_json = {
            "mode": "simple",
            "items": [
                {
                    "description": f"Base cost ({payload.category or 'n/a'})",
                    "qty": computed_qty,
                    "unit_cost": str(per_unit),
                }
            ],
        }

    # 3) markup → pre-fees/tax total
    markup_pct = _resolve_markup_pct(db, payload, computed_qty)
    before_extras = compute_customer_price(subtotal, markup_pct)

    # 4) fees & tax
    fees = Decimal(str(payload.fees or 0)).quantize(DEC2)
    tax  = Decimal(str(payload.tax or 0)).quantize(DEC2)
    grand_total = (before_extras + fees + tax).quantize(DEC2)

    # 5) snapshot
    qn = next_quote_number(db, model_cls=CustomerQuote)
    snapshot = {
        "input": payload.model_dump(mode="json"),
        "calc": {
            "computed_qty": computed_qty,
            "markup_pct": str(markup_pct),
            "subtotal": str(subtotal),
            "before_extras": str(before_extras),
            "fees": str(fees),
            "tax": str(tax),
            "total": str(grand_total),
        },
        "quote_number": qn
    }

    # 6) persist

    row = CustomerQuote(
        quote_number=qn,
        project_id=payload.project_id,
        selected_supplier_quote_id=payload.selected_supplier_quote_id,
        markup_schema_id=schema_id,
        line_items=line_items_json,
        subtotal=subtotal,
        fees=fees,
        tax=tax,
        total=grand_total,
        valid_until=payload.valid_until,
        status=payload.status,
        snapshot=snapshot,
    )

    # Add to database
    db.add(row)
    db.commit()
    db.refresh(row)

    return row