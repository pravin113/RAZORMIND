import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import agent, audit, database, merchants, policies, rag, razorpay, recovery, risk, transactions, webhooks
from app.api.health import router as health_router
from app.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


configure_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled request error",
                extra={"request_id": request_id, "path": request.url.path},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                },
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s completed with %s in %sms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"request_id": request_id},
        )
        return response

    app.include_router(health_router)
    app.include_router(health_router, prefix=settings.api_v1_prefix)
    app.include_router(database.router, prefix=settings.api_v1_prefix)
    app.include_router(merchants.router, prefix=settings.api_v1_prefix)
    app.include_router(transactions.router, prefix=settings.api_v1_prefix)
    app.include_router(razorpay.router, prefix=settings.api_v1_prefix)
    app.include_router(risk.router, prefix=settings.api_v1_prefix)
    app.include_router(recovery.router, prefix=settings.api_v1_prefix)
    app.include_router(audit.router, prefix=settings.api_v1_prefix)
    app.include_router(webhooks.router, prefix=settings.api_v1_prefix)
    app.include_router(policies.router, prefix=settings.api_v1_prefix)
    app.include_router(rag.router, prefix=settings.api_v1_prefix)
    app.include_router(agent.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
