from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.common import ORMModel


class AuditLogCreate(ORMModel):
    merchant_id: UUID | None = None
    actor_type: str
    actor_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    decision: str
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditLogRead(ORMModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    merchant_id: UUID | None
    actor_type: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    decision: str
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime

