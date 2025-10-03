from typing import Iterable, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.schemas import DocumentRead
from app.core.models import Document, DocumentStatus
from app.core.exceptions import DocumentConflictError


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, doc_id: UUID) -> DocumentRead:
        result = await self.session.execute(select(Document).where(Document.document_uuid == doc_id))
        return result.scalar_one_or_none()

    async def add(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def _find_by_name_or_url(
        self, *, name: str, url: str
    ) -> Tuple[Optional[Document], Optional[Document], Optional[Document]]:
        """Returns (exact_match, name_clash, url_clash)."""
        result = await self.session.execute(
            select(Document).where((Document.name == name) | (Document.url == url))
        )
        rows: Iterable[Document] = result.scalars().all()

        exact = name_clash = url_clash = None
        for d in rows:
            if d.name == name and d.url == url:
                exact = d
            elif d.name == name:
                name_clash = d
            elif d.url == url:
                url_clash = d
        return exact, name_clash, url_clash

    async def _set_status(self, doc_id: UUID, status: DocumentStatus) -> None:
        await self.session.execute(
            update(Document)
            .where(Document.document_uuid == doc_id)
            .values(status=status)
        )
        await self.session.commit()

    async def submit_or_resummarize(self, *, name: str, url: str) -> tuple[Document, bool]:
        """
        Smart submission:
          - If exact (same name+url): set to PENDING and return (doc, True)  # re-summarize
          - If name xor url clashes: raise DocumentConflictError
          - Else: create new doc with PENDING and return (doc, False)
        """
        exact, name_clash, url_clash = await self._find_by_name_or_url(name=name, url=url)

        if exact:
            await self._set_status(exact.document_uuid, DocumentStatus.PENDING)
            # get fresh state to return (optional)
            refreshed = await self.get(exact.document_uuid)
            return (refreshed or exact, True)

        if name_clash or url_clash:
            raise DocumentConflictError("Document with same name or URL exists")

        doc = Document(name=name, url=url, status=DocumentStatus.PENDING)
        doc = await self.add(doc)
        return (doc, False)
