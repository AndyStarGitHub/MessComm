from unittest.mock import patch, AsyncMock

import pytest
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

import ai_moderation
from models import User, Posht

from loguru import logger

logger.add("loguru/test_poshts.log")


@pytest.mark.asyncio
async def test_create_posht_unauthorized():
    posht_data = {
        "title": "Unauthorized post",
        "posht_text": "This should not be created",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/poshts/", json=posht_data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.mark.asyncio
async def test_create_post_authorized(async_session: AsyncSession):

    user = User(
        email="testauthorized@example.com",
        hashed_password=pwd_context.hash("testpassword")
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/login",
            data={"username": "testauthorized@example.com", "password": "testpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        posht_data = {
            "title": "Test post",
            "posht_text": "This is a clean post"
        }

        response = await client.post(
            "/poshts/",
            json=posht_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["title"] == "Test post"
        assert result["posht_text"] == "This is a clean post"
        assert result["user_id"] == user.id

import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from main import app


@pytest.mark.asyncio
async def test_create_post_invalid_data_empty_title(async_session):

    user = User(
        email="invalidtitle@example.com",
        hashed_password=pwd_context.hash("strongpassword")
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/login",
            data={"username": "invalidtitle@example.com", "password": "strongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        token = login_response.json()["access_token"]

        invalid_posht = {
            "title": "",
            "posht_text": "Text is acceptable"
        }

        response = await client.post(
            "/poshts/",
            json=invalid_posht,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_post_with_profanity(async_session):
    user = User(
        email="profanity@example.com",
        hashed_password=pwd_context.hash("testpassword")
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    transport = ASGITransport(app=app)

    logger.info("REAL FUNC:", ai_moderation.check_for_profanity)

    with patch("crud.check_for_profanity", new=AsyncMock(return_value=True)):
        logger.info("MOCKED FUNC:", ai_moderation.check_for_profanity)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_response = await client.post(
                "/login",
                data={"username": "profanity@example.com", "password": "testpassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert login_response.status_code == 200
            access_token = login_response.json()["access_token"]

            posht_data = {
                "title": "Test with profanity",
                "posht_text": "This is fucking bullshit."
            }

            response = await client.post(
                "/poshts/",
                json=posht_data,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_blocked"] is True

@pytest.mark.asyncio
async def test_post_author_is_logged_in_user(async_session: AsyncSession):
    user = User(
        email="authorcheck@example.com",
        hashed_password=pwd_context.hash("securepass123")
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/login",
            data={"username": user.email, "password": "securepass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        posht_data = {
            "title": "Author Check Title",
            "posht_text": "This post is for author check."
        }

        response = await client.post(
            "/poshts/",
            json=posht_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        created = response.json()

        stmt = select(Posht).where(Posht.id == created["id"])
        result = await async_session.execute(stmt)
        posht = result.scalar_one()

        assert posht.user_id == user.id
