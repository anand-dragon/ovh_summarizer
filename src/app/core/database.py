from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
