from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.workflows import (
    RecoveryOutcomeRead,
    RevenueRecoveryOrchestrator,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
)
from app.db.session import get_db
from app.schemas.analysis import RecoveryAnalysisResponse, RecoverySummary, TransactionAnalysisInput
from app.schemas.recovery import RecoveryOpportunityRead
from app.services.ml_analysis import get_recovery_summary, run_recovery_analysis
from app.services.recovery import list_recovery_opportunities

router = APIRouter(prefix="/recovery", tags=["recovery"])


@router.get("/opportunities", response_model=list[RecoveryOpportunityRead])
async def get_recovery_opportunities(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_recovery_opportunities(db, offset=offset, limit=limit)


@router.post("/analyze", response_model=RecoveryAnalysisResponse)
async def post_recovery_analysis(payload: TransactionAnalysisInput, db: Session = Depends(get_db)):
    try:
        return run_recovery_analysis(db, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Recovery model artifacts are not available") from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Recovery analysis could not be persisted") from exc


@router.get("/summary", response_model=RecoverySummary)
async def recovery_summary(db: Session = Depends(get_db)):
    return get_recovery_summary(db)


@router.post("/execute", response_model=WorkflowExecuteResponse)
async def execute_autonomous_recovery(
    payload: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
):
    orchestrator = RevenueRecoveryOrchestrator(db)
    return orchestrator.execute_recovery(payload)


@router.get("/outcomes", response_model=list[RecoveryOutcomeRead])
async def list_recovery_outcomes(
    merchant_id: UUID | None = Query(default=None, description="Filter outcomes by merchant"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    orchestrator = RevenueRecoveryOrchestrator(db)
    return orchestrator.list_outcomes(merchant_id=merchant_id, offset=offset, limit=limit)


@router.get("/workflows/{outcome_id}", response_model=RecoveryOutcomeRead)
async def get_workflow_outcome(
    outcome_id: UUID,
    db: Session = Depends(get_db),
):
    orchestrator = RevenueRecoveryOrchestrator(db)
    outcome = orchestrator.get_outcome(outcome_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow outcome not found",
        )
    return outcome

