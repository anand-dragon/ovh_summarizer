from typing import Optional, Type
from types import TracebackType

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.models import Document, DocumentStatus
from app.core.config import DATABASE_URL


# Async engine & session factory
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class WorkerDocumentRepository:
    def __init__(self, session: Optional[AsyncSession] = None):
        self._external_session = session
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self) -> "WorkerDocumentRepository":
        if self._external_session:
            self._session = self._external_session
        else:
            self._session = AsyncSessionLocal()
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[TracebackType],
    ) -> None:
        if not self._external_session and self._session:
            await self._session.close()

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def get_by_id(self, document_uuid: str) -> Optional[Document]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Document).where(Document.document_uuid == document_uuid))
            return result.scalar_one_or_none()

    async def update_status(self, document_uuid: str, status: DocumentStatus) -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(update(Document).where(Document.document_uuid == document_uuid).values(status=status))
            await session.commit()

    async def update_summary(self, document_uuid: str, summary: str, status: DocumentStatus) -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Document).where(Document.document_uuid == document_uuid).values(summary=summary, status=status)
            )
            await session.commit()
