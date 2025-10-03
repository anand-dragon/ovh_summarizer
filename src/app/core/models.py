import enum
import uuid

from sqlalchemy import Column, Enum, String, Text, DateTime, func
from sqlalchemy.sql.functions import now
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    document_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(Enum(DocumentStatus), nullable=False) # type: ignore
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.timezone("utc", now()))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.timezone("utc", now()))
