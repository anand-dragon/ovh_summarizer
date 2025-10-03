import logging
from typing import Any, MutableMapping
import os
from app.core.models import DocumentStatus


from app.worker.domain.worker_document_repository import WorkerDocumentRepository
from app.worker.utils import call_ollama, fetch_and_extract

from arq.connections import RedisSettings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s — %(message)s [%(pathname)s:%(lineno)d]"
)

logger = logging.getLogger("app")


async def startup(ctx: MutableMapping[str, Any]) -> None:
    ctx["document_repo"] = WorkerDocumentRepository()


async def shutdown(ctx: MutableMapping[str, Any]) -> None:
    document_repo: WorkerDocumentRepository = ctx.get("document_repo")
    if document_repo:
        await document_repo.close()


async def process_document(ctx: MutableMapping[str, Any], document_uuid: str) -> None:
    """
    Worker task to fetch, summarize, and update a document.
    """
    document_repo: WorkerDocumentRepository = ctx["document_repo"]

    document = await document_repo.get_by_id(document_uuid)
    if not document:
        logger.info(f"[Worker] Document {document_uuid} not found")
        return

    await document_repo.update_status(document_uuid, DocumentStatus.PROCESSING)

    try:
        content = await fetch_and_extract(document.url)
        summary = await call_ollama(content)

        await document_repo.update_summary(document_uuid, summary=summary, status=DocumentStatus.SUCCESS)

    except Exception as e:
        logger.info(f"[Worker] Failed to process document {document_uuid}: {e}")
        await document_repo.update_status(document_uuid, DocumentStatus.FAILED)


class WorkerSettings:
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", "6379")), database=0
    )
    functions = [process_document]
    max_jobs = 10
    on_startup = startup
    on_shutdown = shutdown
