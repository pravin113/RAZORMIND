from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLog
from app.schemas.audit import AuditLogCreate


def create_audit_log(db: Session, payload: AuditLogCreate) -> AuditLog:
    data = payload.model_dump()
    data["metadata_"] = data.pop("metadata")
    audit_log = AuditLog(**data)
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def list_audit_logs(db: Session, offset: int = 0, limit: int = 100) -> list[AuditLog]:
    statement = select(AuditLog).offset(offset).limit(limit).order_by(AuditLog.created_at.desc())
    return list(db.scalars(statement).all())

