import os
from fastapi import Depends
from arq.connections import ArqRedis, create_pool, RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.api.domain.document_repository import DocumentRepository

async def get_session() -> AsyncSession:  # type: ignore
    async with AsyncSessionLocal() as session:
        yield session


async def get_document_repository(session: AsyncSession = Depends(get_session)) -> DocumentRepository:
    return DocumentRepository(session)


# Redis Singleton
_redis: ArqRedis | None = None


async def init_redis_pool() -> ArqRedis:
    """Initialize the Redis pool once at startup."""
    global _redis
    if not _redis:
        settings = RedisSettings(
            host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", "6379")), database=0
        )
        _redis = await create_pool(settings)
    return _redis


async def close_redis_pool() -> None:
    """Close the Redis pool at shutdown."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def get_redis() -> ArqRedis:
    """Dependency for injecting the Redis connection into routes."""
    if not _redis:
        raise RuntimeError("Redis not initialized! Make sure to call init_redis_pool() at startup.")
    return _redis
