from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./messcomm.db"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, future=True
)


async def get_db() -> AsyncGenerator:
    async with SessionLocal() as session:
        yield session
