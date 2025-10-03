from typing import Optional
from uuid import UUID

from pydantic import BaseModel, computed_field

from app.core.models import DocumentStatus


class DocumentCreate(BaseModel):
    name: str
    url: str


class DocumentRead(BaseModel):
    document_uuid: UUID
    name: str
    url: str
    summary: Optional[str] = None
    status: DocumentStatus

    @computed_field(return_type=float)
    def data_progress(self) -> float:
        match self.status:
            case DocumentStatus.PENDING:
                return 0.0
            case DocumentStatus.PROCESSING:
                return 0.5
            case DocumentStatus.SUCCESS:
                return 1.0
            case DocumentStatus.FAILED:
                return -1.0
        return 0.0

    class Config:
        from_attributes = True
