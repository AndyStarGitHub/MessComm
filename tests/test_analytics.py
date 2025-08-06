from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from models import Comment, Posht, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.mark.asyncio
async def test_comment_analytics_empty(async_session: AsyncSession) -> None:
    user = User(
        email="analytics1@example.com", hashed_password=pwd_context.hash("testpassword")
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/login",
            data={"username": "analytics1@example.com", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = await client.get(
            "/analytics/comments/", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_comments_analytics_multiple_days(async_session: AsyncSession) -> None:
    async with async_session as session:
        user = User(email="analytics2@example.com", hashed_password="123")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        posht = Posht(title="Analytics test", posht_text="Test", user_id=user.id)
        session.add(posht)
        await session.commit()
        await session.refresh(posht)

        yesterday = datetime.now() - timedelta(days=1)
        two_days_ago = datetime.now() - timedelta(days=2)

        comments = [
            Comment(
                comment_text="Normal",
                is_blocked=False,
                user_id=user.id,
                posht_id=posht.id,
                created_at=two_days_ago,
            ),
            Comment(
                comment_text="Blocked",
                is_blocked=True,
                user_id=user.id,
                posht_id=posht.id,
                created_at=yesterday,
            ),
            Comment(
                comment_text="Normal 2",
                is_blocked=False,
                user_id=user.id,
                posht_id=posht.id,
                created_at=yesterday,
            ),
        ]
        session.add_all(comments)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/analytics/comments/")
        assert response.status_code == 200
        data = response.json()

        assert any(
            entry["date"] == yesterday.date().isoformat()
            and entry["count"] == 2
            and entry["blocked_count"] == 1
            for entry in data
        )

        assert any(
            entry["date"] == two_days_ago.date().isoformat()
            and entry["count"] == 1
            and entry["blocked_count"] == 0
            for entry in data
        )
