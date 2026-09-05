from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RiskScore
from app.schemas.risk import RiskScoreCreate


def create_risk_score(db: Session, payload: RiskScoreCreate) -> RiskScore:
    risk_score = RiskScore(**payload.model_dump())
    db.add(risk_score)
    db.commit()
    db.refresh(risk_score)
    return risk_score


def list_risk_scores_for_transaction(db: Session, transaction_id: UUID) -> list[RiskScore]:
    statement = (
        select(RiskScore)
        .where(RiskScore.transaction_id == transaction_id)
        .order_by(RiskScore.created_at.desc())
    )
    return list(db.scalars(statement).all())

