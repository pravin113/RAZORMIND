from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RecoveryOpportunity
from app.schemas.recovery import RecoveryOpportunityCreate


def create_recovery_opportunity(
    db: Session,
    payload: RecoveryOpportunityCreate,
) -> RecoveryOpportunity:
    opportunity = RecoveryOpportunity(**payload.model_dump())
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


def list_recovery_opportunities(
    db: Session,
    offset: int = 0,
    limit: int = 100,
) -> list[RecoveryOpportunity]:
    statement = (
        select(RecoveryOpportunity)
        .offset(offset)
        .limit(limit)
        .order_by(RecoveryOpportunity.created_at.desc())
    )
    return list(db.scalars(statement).all())

