from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.razorpay import WebhookResponse
from app.services.webhook_service import (
    WebhookProcessingError,
    WebhookSecretNotConfigured,
    WebhookSignatureError,
    process_razorpay_webhook,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/razorpay", response_model=WebhookResponse)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
    x_razorpay_event_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    try:
        return process_razorpay_webhook(
            db=db,
            raw_body=raw_body,
            signature=x_razorpay_signature,
            event_id=x_razorpay_event_id,
        )
    except WebhookSecretNotConfigured as exc:
        raise HTTPException(status_code=503, detail="Razorpay webhook secret is not configured") from exc
    except WebhookSignatureError as exc:
        raise HTTPException(status_code=401, detail="Invalid Razorpay webhook signature") from exc
    except WebhookProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

