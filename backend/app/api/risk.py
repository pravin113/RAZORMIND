from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import RiskAnalysisResponse, RiskSummary, TransactionAnalysisInput
from app.schemas.risk import RiskScoreRead
from app.services.ml_analysis import get_risk_summary, run_risk_analysis
from app.services.risk_scores import list_risk_scores_for_transaction

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/scores/{transaction_id}", response_model=list[RiskScoreRead])
async def get_risk_scores(transaction_id: UUID, db: Session = Depends(get_db)):
    return list_risk_scores_for_transaction(db, transaction_id)


@router.post("/analyze", response_model=RiskAnalysisResponse)
async def post_risk_analysis(payload: TransactionAnalysisInput, db: Session = Depends(get_db)):
    try:
        return run_risk_analysis(db, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Risk model artifacts are not available") from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Risk analysis could not be persisted") from exc


@router.get("/summary", response_model=RiskSummary)
async def risk_summary(db: Session = Depends(get_db)):
    return get_risk_summary(db)
