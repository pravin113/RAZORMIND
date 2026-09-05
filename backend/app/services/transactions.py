from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Transaction
from app.schemas.transaction import TransactionCreate


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    data = payload.model_dump()
    data["metadata_"] = data.pop("metadata")
    transaction = Transaction(**data)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_transaction(db: Session, transaction_id: UUID) -> Transaction | None:
    return db.get(Transaction, transaction_id)


def list_transactions(db: Session, offset: int = 0, limit: int = 100) -> list[Transaction]:
    statement = select(Transaction).offset(offset).limit(limit).order_by(Transaction.created_at.desc())
    return list(db.scalars(statement).all())

