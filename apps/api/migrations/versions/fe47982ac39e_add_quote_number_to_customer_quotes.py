"""add quote_number to customer_quotes

Revision ID: fe47982ac39e
Revises: dd871dd24d18
Create Date: 2025-11-08 21:55:22.060698

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe47982ac39e'
down_revision: Union[str, Sequence[str], None] = 'dd871dd24d18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1) Add column nullable for now
    op.add_column(
        "customer_quotes",
        sa.Column("quote_number", sa.String(length=32), nullable=True)
    )
    # 2) Create an index (will be made unique after backfill)
    op.create_index(
        "ix_customer_quotes_quote_number",
        "customer_quotes",
        ["quote_number"],
        unique=False,
    )

    # 3) Backfill with Q-YYYYMM-#### using created_at + per-month sequence
    #    We use a CTE with window function and then UPDATE from it.
    bind = op.get_bind()
    bind.execute(sa.text("""
        WITH numbered AS (
            SELECT
                id,
                'QUOTE-' || to_char(created_at, 'YYYYMM') || '-' ||
                lpad((row_number() OVER (
                    PARTITION BY to_char(created_at, 'YYYYMM')
                    ORDER BY id
                ))::text, 4, '0') AS qn
            FROM customer_quotes
        )
        UPDATE customer_quotes cq
        SET quote_number = numbered.qn
        FROM numbered
        WHERE cq.id = numbered.id
          AND cq.quote_number IS NULL;
    """))

    # 4) Add a format constraint
    op.execute(sa.text("""
        ALTER TABLE customer_quotes
        ADD CONSTRAINT chk_quote_number_format
        CHECK (quote_number ~ '^QUOTE-[0-9]{6}-[0-9]{4}$');
    """))

    # 5) Add a unique constraint
    op.create_unique_constraint(
        "uq_customer_quotes_quote_number",
        "customer_quotes",
        ["quote_number"],
    )

    # 6) Make column NOT NULL (now that all rows have a value)
    op.alter_column(
        "customer_quotes",
        "quote_number",
        existing_type=sa.String(length=32),
        nullable=False
    )

    pass


def downgrade() -> None:
    """Downgrade schema."""

     # Drop unique constraint + index + column in reverse order

    op.drop_constraint("uq_customer_quotes_quote_number", "customer_quotes", type_="unique")
    op.drop_constraint("chk_quote_number_format", "customer_quotes", type_="check")
    op.drop_index("ix_customer_quotes_quote_number", table_name="customer_quotes")
    op.drop_column("customer_quotes", "quote_number")

    pass
