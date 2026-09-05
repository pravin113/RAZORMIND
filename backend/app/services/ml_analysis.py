from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.recovery.predict import predict_recovery
from app.ai.risk_engine import analyze_risk
from app.db.models import FraudEvent, RecoveryOpportunity, RiskScore
from app.schemas.analysis import TransactionAnalysisInput


def _payload_dict(payload: TransactionAnalysisInput) -> dict:
    data = payload.model_dump()
    data["amount"] = float(data["amount"])
    if data.get("customer_avg_amount") is None:
        data["customer_avg_amount"] = data["amount"]
    if data.get("merchant_avg_amount") is None:
        data["merchant_avg_amount"] = data["amount"]
    data["customer_avg_amount"] = float(data["customer_avg_amount"])
    data["merchant_avg_amount"] = float(data["merchant_avg_amount"])
    data["customer_value"] = float(data["customer_value"])
    return data


def run_risk_analysis(db: Session, payload: TransactionAnalysisInput) -> dict:
    result = analyze_risk(_payload_dict(payload))
    if payload.transaction_id:
        risk_score = RiskScore(
            transaction_id=payload.transaction_id,
            fraud_probability=Decimal(str(result["fraud_probability"])),
            anomaly_score=Decimal(str(result["anomaly_score"])),
            risk_score=Decimal(str(result["risk_score"])),
            risk_level=result["risk_level"],
            model_version=result["model_version"],
        )
        db.add(risk_score)
        if result["risk_level"] in {"HIGH", "CRITICAL"}:
            db.add(
                FraudEvent(
                    transaction_id=payload.transaction_id,
                    risk_score=risk_score,
                    event_type="ml_risk_flag",
                    severity=result["risk_level"],
                    amount_at_risk=payload.amount,
                    reason="ML risk analysis exceeded high-risk threshold",
                    status="open",
                )
            )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise
    return result


def run_recovery_analysis(db: Session, payload: TransactionAnalysisInput) -> dict:
    result = predict_recovery(_payload_dict(payload))
    if payload.transaction_id or payload.customer_id:
        opportunity = RecoveryOpportunity(
            transaction_id=payload.transaction_id,
            customer_id=payload.customer_id,
            opportunity_type="payment_recovery",
            amount_at_risk=payload.amount,
            recovery_probability=Decimal(str(result["recovery_probability"])),
            priority=result["recommended_priority"],
            status="open",
            recommended_action="Prioritize recovery outreach based on predicted recovery probability",
        )
        db.add(opportunity)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise
    return result


def get_risk_summary(db: Session) -> dict:
    total = db.scalar(select(func.count(RiskScore.id))) or 0
    average = db.scalar(select(func.avg(RiskScore.risk_score))) or 0
    level_rows = db.execute(select(RiskScore.risk_level, func.count(RiskScore.id)).group_by(RiskScore.risk_level)).all()
    return {
        "total_risk_scores": total,
        "average_risk_score": float(average),
        "by_risk_level": {level: count for level, count in level_rows},
    }


def get_recovery_summary(db: Session) -> dict:
    total = db.scalar(select(func.count(RecoveryOpportunity.id))) or 0
    open_total = db.scalar(select(func.count(RecoveryOpportunity.id)).where(RecoveryOpportunity.status == "open")) or 0
    average = db.scalar(select(func.avg(RecoveryOpportunity.recovery_probability))) or 0
    value = db.scalar(
        select(func.sum(RecoveryOpportunity.amount_at_risk * RecoveryOpportunity.recovery_probability))
    ) or 0
    return {
        "total_opportunities": total,
        "open_opportunities": open_total,
        "average_recovery_probability": float(average),
        "expected_recovered_value": Decimal(str(value)),
    }

