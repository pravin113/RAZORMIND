from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Merchant
from app.schemas.merchant import MerchantCreate


def create_merchant(db: Session, payload: MerchantCreate) -> Merchant:
    merchant = Merchant(**payload.model_dump())
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def list_merchants(db: Session, offset: int = 0, limit: int = 100) -> list[Merchant]:
    statement = select(Merchant).offset(offset).limit(limit).order_by(Merchant.created_at.desc())
    return list(db.scalars(statement).all())

