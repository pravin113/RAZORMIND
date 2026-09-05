from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.merchant import MerchantCreate, MerchantRead
from app.services.merchants import create_merchant, list_merchants

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.get("", response_model=list[MerchantRead])
async def get_merchants(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_merchants(db, offset=offset, limit=limit)


@router.post("", response_model=MerchantRead, status_code=201)
async def post_merchant(payload: MerchantCreate, db: Session = Depends(get_db)):
    try:
        return create_merchant(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Merchant could not be created") from exc

