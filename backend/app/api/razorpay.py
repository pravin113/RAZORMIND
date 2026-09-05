from fastapi import APIRouter, Depends, HTTPException

from app.schemas.razorpay import (
    RazorpayOrderCreate,
    RazorpayOrderResponse,
    RazorpayPaymentResponse,
    RazorpayPaymentsResponse,
    RazorpayStatusResponse,
)
from app.services.razorpay_service import (
    RazorpayConfigurationError,
    RazorpayService,
    RazorpayServiceError,
    get_razorpay_service,
)

router = APIRouter(prefix="/razorpay", tags=["razorpay"])


@router.get("/status", response_model=RazorpayStatusResponse)
async def razorpay_status(service: RazorpayService = Depends(get_razorpay_service)):
    return {"configured": service.configured, "mode": "test"}


@router.post("/orders", response_model=RazorpayOrderResponse, status_code=201)
async def create_order(
    payload: RazorpayOrderCreate,
    service: RazorpayService = Depends(get_razorpay_service),
):
    try:
        return service.create_order(
            amount=payload.amount,
            currency=payload.currency,
            receipt=payload.receipt,
            notes=payload.notes,
        )
    except RazorpayConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Razorpay test credentials are not configured") from exc
    except RazorpayServiceError as exc:
        raise HTTPException(status_code=502, detail="Razorpay API request failed") from exc


@router.get("/orders/{order_id}", response_model=RazorpayOrderResponse)
async def fetch_order(order_id: str, service: RazorpayService = Depends(get_razorpay_service)):
    try:
        return service.fetch_order(order_id)
    except RazorpayConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Razorpay test credentials are not configured") from exc
    except RazorpayServiceError as exc:
        raise HTTPException(status_code=502, detail="Razorpay API request failed") from exc


@router.get("/payments/{payment_id}", response_model=RazorpayPaymentResponse)
async def fetch_payment(payment_id: str, service: RazorpayService = Depends(get_razorpay_service)):
    try:
        return service.fetch_payment(payment_id)
    except RazorpayConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Razorpay test credentials are not configured") from exc
    except RazorpayServiceError as exc:
        raise HTTPException(status_code=502, detail="Razorpay API request failed") from exc


@router.get("/orders/{order_id}/payments", response_model=RazorpayPaymentsResponse)
async def fetch_order_payments(order_id: str, service: RazorpayService = Depends(get_razorpay_service)):
    try:
        return service.fetch_order_payments(order_id)
    except RazorpayConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Razorpay test credentials are not configured") from exc
    except RazorpayServiceError as exc:
        raise HTTPException(status_code=502, detail="Razorpay API request failed") from exc

