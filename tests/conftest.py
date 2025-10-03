import datetime as dt
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.api.main import app
from app.core.models import Document, DocumentStatus
from app.api.domain.document_repository import DocumentRepository
from app.core.exceptions import DocumentConflictError
from app.api import depends


# ---------------------------
# In-memory fake repositories
# ---------------------------

class FakeDocumentRepository(DocumentRepository):
    """In-memory replacement for DocumentRepository (no DB)."""

    def __init__(self) -> None:  # ignore the real session
        self._store: Dict[uuid.UUID, Document] = {}

    async def add(self, doc: Document) -> Document:
        if not getattr(doc, "document_uuid", None):
            doc.document_uuid = uuid.uuid4()
        now = dt.datetime.now(dt.timezone.utc)
        if not getattr(doc, "created_at", None):
            doc.created_at = now
        doc.updated_at = now
        self._store[doc.document_uuid] = doc
        return doc

    async def get(self, doc_id: uuid.UUID) -> Optional[Document]:
        if isinstance(doc_id, str):
            try:
                doc_id = uuid.UUID(doc_id)
            except Exception:
                return None
        return self._store.get(doc_id)

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> List[Document]:
        docs = sorted(self._store.values(), key=lambda d: d.created_at, reverse=True)
        return docs[offset : offset + limit]

    async def _set_status(self, doc_id: uuid.UUID, status: DocumentStatus) -> None:
        doc = await self.get(doc_id)
        if doc:
            doc.status = status
            doc.updated_at = dt.datetime.now(dt.timezone.utc)

    async def submit_or_resummarize(self, *, name: str, url: str) -> tuple[Document, bool]:
        """
        - If exact (same name+url): set to PENDING and return (doc, True)
        - If name xor url clashes: raise DocumentConflictError
        - Else: create new PENDING doc and return (doc, False)
        """
        exact = None
        name_clash = None
        url_clash = None

        for d in self._store.values():
            if d.name == name and d.url == url:
                exact = d
            elif d.name == name:
                name_clash = d
            elif d.url == url:
                url_clash = d

        if exact:
            await self._set_status(exact.document_uuid, DocumentStatus.PENDING)
            return exact, True

        if name_clash or url_clash:
            raise DocumentConflictError("Document with same name or URL exists")

        new_doc = Document(name=name, url=url, summary=None, status=DocumentStatus.PENDING)
        new_doc = await self.add(new_doc)
        return new_doc, False

# Dummy Redis for API routes
class _DummyRedis:
    async def ping(self) -> bool:
        return True

    async def enqueue_job(self, *_: Any, **__: Any) -> None:
        return None


# ---------------------------
# FastAPI test client fixture
# ---------------------------

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    fake_repo = FakeDocumentRepository()

    def _get_repo_override() -> DocumentRepository:
        return fake_repo

    async def _get_redis_override():
        return _DummyRedis()

    app.dependency_overrides[depends.get_document_repository] = _get_repo_override
    app.dependency_overrides[depends.get_redis] = _get_redis_override

    async with AsyncClient(app=app, base_url="http://testserver", follow_redirects=True) as ac:
        try:
            yield ac
        finally:
            app.dependency_overrides.clear()



# ---------------------------
# Worker-side in-memory repo
# ---------------------------

class FakeWorkerDocumentRepository:
    """Minimal in-memory repo for the worker task."""
    def __init__(self) -> None:
        self._store: Dict[uuid.UUID, Document] = {}

    async def close(self) -> None:
        return

    async def get_by_id(self, document_uuid: str) -> Optional[Document]:
        try:
            key = uuid.UUID(document_uuid)
        except Exception:
            return None
        return self._store.get(key)

    async def update_status(self, document_uuid: str, status: DocumentStatus) -> None:
        doc = await self.get_by_id(document_uuid)
        if doc:
            doc.status = status
            doc.updated_at = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)

    async def update_summary(self, document_uuid: str, summary: str, status: DocumentStatus) -> None:
        doc = await self.get_by_id(document_uuid)
        if doc:
            doc.summary = summary
            doc.status = status
            doc.updated_at = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)

    # Helper for tests to seed a doc
    async def add(self, doc: Document) -> Document:
        if not getattr(doc, "document_uuid", None):
            doc.document_uuid = uuid.uuid4()
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
        doc.created_at = getattr(doc, "created_at", now) or now
        doc.updated_at = now
        self._store[doc.document_uuid] = doc
        return doc


@pytest.fixture
def fake_worker_repo() -> FakeWorkerDocumentRepository:
    return FakeWorkerDocumentRepository()
