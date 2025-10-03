from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from arq.connections import ArqRedis

from app.api.domain.document_repository import DocumentRepository
from app.core.schemas import DocumentCreate, DocumentRead
from app.core.models import Document
from app.core.exceptions import DocumentConflictError

from .. import depends

router = APIRouter()


@router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentRead)
async def create_document(
    payload: DocumentCreate,
    repo: DocumentRepository = Depends(depends.get_document_repository),
    redis: ArqRedis = Depends(depends.get_redis),
) -> DocumentRead:
    try:
        doc, _resummarized = await repo.submit_or_resummarize(name=payload.name, url=payload.url)
    except DocumentConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    await redis.enqueue_job("process_document", str(doc.document_uuid))
    return doc


@router.get("/", response_model=list[DocumentRead])
async def list_documents(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    repo: DocumentRepository = Depends(depends.get_document_repository),
) -> list[DocumentRead]:
    docs: list[Document] = await repo.list_all(limit=limit, offset=offset)
    return [DocumentRead.model_validate(d) for d in docs]


@router.get("/{document_uuid}/", response_model=DocumentRead)
async def get_document(
    document_uuid: str,
    repo: DocumentRepository = Depends(depends.get_document_repository)
) -> DocumentRead:
    doc = await repo.get(document_uuid)
    return doc


@router.get("/health")
async def redis_health(redis: ArqRedis = Depends(depends.get_redis)) -> dict[str, Any]:
    pong = await redis.ping()
    return {"redis_alive": pong}
