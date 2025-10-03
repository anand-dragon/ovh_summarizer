import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI

from app.api.routers import router_documents
from app.core.middleware import LoggingMiddleware
from .depends import init_redis_pool, close_redis_pool

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s — %(message)s [%(pathname)s:%(lineno)d]"
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_redis_pool()
    yield
    await close_redis_pool()


app = FastAPI(title="Summarizer API", lifespan=lifespan)

app.add_middleware(LoggingMiddleware)

app.include_router(router_documents.router, prefix="/documents", tags=["documents"])
