from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.transaction import TransactionCreate, TransactionRead
from app.services.transactions import create_transaction, get_transaction, list_transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
async def get_transactions(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_transactions(db, offset=offset, limit=limit)


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction_by_id(transaction_id: UUID, db: Session = Depends(get_db)):
    transaction = get_transaction(db, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.post("", response_model=TransactionRead, status_code=201)
async def post_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    try:
        return create_transaction(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Transaction could not be created") from exc

