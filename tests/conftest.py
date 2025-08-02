import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db
from models import Base
from main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        yield session

    await engine.dispose()
