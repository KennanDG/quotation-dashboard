from __future__ import annotations
from datetime import datetime
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

def next_quote_number(db: Session, *, model_cls, column_name: str = "quote_number") -> str:
    """
    Generate a quote number like QUOTE-YYYYMM-#### (zero-padded sequence).
    Looks only at the current month to increment the last 4 digits.
    This is application-side; add a unique index on quote_number.

    Args:
        db: SQLAlchemy session.
        model_cls: ORM class that has the quote number column.
        column_name: Name of the quote number column on the model.

    Returns:
        str: e.g., "QUOTE-202511-0007"
    """
    now = datetime.utcnow()
    prefix = f"QUOTE-{now:%Y%m}-"
    col = getattr(model_cls, column_name)

    # Find the max quote number with this month’s prefix
    last = (
        db.query(func.max(col))
          .filter(col.like(prefix + "%"))
          .scalar()
    )

    if last:
        try:
            n = int(last.split("-")[-1])
        except Exception:
            n = 0
    else:
        n = 0

    return f"{prefix}{n+1:04d}"