from unittest.mock import AsyncMock, patch
import pytest

from app.worker.tasks import process_document
from app.core.models import Document, DocumentStatus

@pytest.mark.asyncio
@patch("app.worker.tasks.call_ollama", new_callable=AsyncMock)
@patch("app.worker.tasks.fetch_and_extract", new_callable=AsyncMock)
async def test_worker_task_updates_doc(mock_fetch, mock_ollama, fake_worker_repo):
    mock_fetch.return_value = "Some fetched content"
    mock_ollama.return_value = "Summarized text"

    doc = Document(name="Seed", url="https://seed.test", summary=None, status=DocumentStatus.PENDING)
    await fake_worker_repo.add(doc)

    ctx = {"document_repo": fake_worker_repo}
    await process_document(ctx, str(doc.document_uuid))

    mock_fetch.assert_called_once()
    mock_ollama.assert_called_once()

    updated = await fake_worker_repo.get_by_id(str(doc.document_uuid))
    assert updated is not None
    assert updated.status == DocumentStatus.SUCCESS
    assert updated.summary == "Summarized text"
