from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from database import SessionLocal
from schemas.models import (
    User, Project, RFQ, SupplierQuote, InternalEstimate, MarkupSchema,
    ServiceType, Role
)


def upsert_user(db, *, email: str, name: str, role: Role) -> int:
    
    stmt = insert(User).values(email=email, name=name, role=role)

    stmt = stmt.on_conflict_do_update(
        index_elements=[User.email],  # email is unique
        set_=dict(name=name, role=role)
    ).returning(User.id)

    return db.execute(stmt).scalar_one()



def upsert_markup_schema(db, *, name: str, rules: dict) -> int:
    
    stmt = insert(MarkupSchema).values(name=name, is_active=True, rules=rules)

    stmt = stmt.on_conflict_do_update(
        index_elements=[MarkupSchema.name],  # name is unique
        set_=dict(is_active=True, rules=rules)
    ).returning(MarkupSchema.id)

    return db.execute(stmt).scalar_one()



def ensure_project(db, *, name: str, service_type: ServiceType, client_name: str | None, owner_id: int | None) -> int:
    
    existing = db.execute(select(Project.id).where(Project.name == name)).scalar_one_or_none()
    
    if existing:
        return existing
   
    proj = Project(
        name=name,
        client_name=client_name,
        service_type=service_type,
        status="draft",
        owner_id=owner_id,
        intake={"source": "seed"},
        calc_snapshot=None,
    )
    
    db.add(proj)
    db.flush()

    return proj.id


def create_rfq_if_missing(db, *, project_id: int, created_by: int, assigned_to: int | None) -> int:
    
    rfq_id = db.execute(
        select(RFQ.id).where(RFQ.project_id == project_id)
    ).scalar_one_or_none()

    if rfq_id:
        return rfq_id
    
    rfq = RFQ(
        project_id=project_id,
        created_by=created_by,
        assigned_to=assigned_to,
        requirements={"material": "ABS", "finish": "natural", "notes": "MVP sample"},
        status="collecting",
        due_date=datetime.utcnow() + timedelta(days=10),
    )

    db.add(rfq)
    db.flush()

    return rfq.id



def add_supplier_quotes_if_missing(db, *, rfq_id: int):

    existing = db.execute(select(SupplierQuote.id).where(SupplierQuote.rfq_id == rfq_id)).first()

    if existing:
        return
    
    q1 = SupplierQuote(
        rfq_id=rfq_id,
        supplier_name="Alpha Plastics Co.",
        currency="USD",
        tooling_cost=Decimal("3500.00"),
        unit_price=Decimal("2.4500"),
        moq=100,
        lead_time_days=21,
        notes="Standard steel mold, single cavity.",
        raw={"email": "sales@alphaplastics.example", "rev": "A"},
        status="received"
    )

    q2 = SupplierQuote(
        rfq_id=rfq_id,
        supplier_name="Beta Mold & Tool",
        currency="USD",
        tooling_cost=Decimal("4800.00"),
        unit_price=Decimal("2.1000"),
        moq=250,
        lead_time_days=28,
        notes="Hardened steel, textured finish.",
        raw={"portal_id": "Q-78231"},
        status="received"
    )

    db.add_all([q1, q2])



def add_internal_estimates_if_missing(db, *, project_id: int):
    existing = db.execute(select(InternalEstimate.id).where(InternalEstimate.project_id == project_id)).first()
    if existing:
        return
    rows = [
        InternalEstimate(
            project_id=project_id,
            category="labor",
            description="DFM review & RFQ prep",
            qty=Decimal("4"),
            rate=Decimal("85.00"),
            amount=Decimal("340.00"),
            meta={"role": "PM"}
        ),
        InternalEstimate(
            project_id=project_id,
            category="shipping",
            description="Inbound materials",
            qty=Decimal("1"),
            rate=Decimal("120.00"),
            amount=Decimal("120.00"),
            meta={"carrier": "UPS"}
        ),
    ]
    db.add_all(rows)



def run():
    db = SessionLocal()
    try:
        # 1) Users
        admin_id = upsert_user(db, email="pm.admin@jaycon.local", name="PM Admin", role=Role.ADMIN)
        pm_id    = upsert_user(db, email="pm.user@jaycon.local",  name="Project Manager", role=Role.PM)

        # 2) Markup schema (JSON rules by service w/ qty bands)
        rules = {
            "im": {  # injection molding
                "bands": [
                    {"min_qty": 1,   "max_qty": 49,  "markup_percent": "35.0"},
                    {"min_qty": 50,  "max_qty": 199, "markup_percent": "28.0"},
                    {"min_qty": 200, "max_qty": 999, "markup_percent": "22.0"},
                    {"min_qty": 1000, "max_qty": None, "markup_percent": "18.0"},
                ]
            },
            "cnc_machining": {
                "bands": [
                    {"min_qty": 1,  "max_qty": 9,   "markup_percent": "30.0"},
                    {"min_qty": 10, "max_qty": 49,  "markup_percent": "24.0"},
                    {"min_qty": 50, "max_qty": None, "markup_percent": "18.0"},
                ]
            },
            "pcba": {
                "bands": [
                    {"min_qty": 1,   "max_qty": 49,  "markup_percent": "25.0"},
                    {"min_qty": 50,  "max_qty": 199, "markup_percent": "20.0"},
                    {"min_qty": 200, "max_qty": None, "markup_percent": "15.0"},
                ]
            },
            "design": {
                "bands": [
                    {"min_qty": 1, "max_qty": None, "markup_percent": "12.0"}  # flat
                ]
            }
        }
        markup_id = upsert_markup_schema(db, name="Default Schema", rules=rules)

        # 3) Project
        proj_id = ensure_project(
            db,
            name="MVP Injection Molded Bracket",
            service_type=ServiceType.im,
            client_name="Acme Robotics",
            owner_id=pm_id,
        )

        # 4) RFQ
        rfq_id = create_rfq_if_missing(db, project_id=proj_id, created_by=pm_id, assigned_to=admin_id)

        # 5) Supplier quotes
        add_supplier_quotes_if_missing(db, rfq_id=rfq_id)

        # 6) Internal estimates
        add_internal_estimates_if_missing(db, project_id=proj_id)

        db.commit()
        print("Seed complete.")
        print(f"  Users: admin={admin_id}, pm={pm_id}")
        print(f"  Markup schema id={markup_id}")
        print(f"  Project id={proj_id}, RFQ id={rfq_id}")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()