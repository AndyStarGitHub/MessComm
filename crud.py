import asyncio
from datetime import datetime, timedelta
from typing import Sequence

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_moderation import check_for_profanity, model
from config import ALGORITHM, PROMPT_FOR_AUTO_REPLY, SECRET_KEY
from database import get_db
from loguru import logger
from models import Comment, Posht, User
from schemas import (
    CommentCreate,
    CommentUpdate,
    PoshtCreate,
    PoshtUpdate,
    UserCreate,
    UserRead,
)
from security import decode_token, hash_password

logger.add("loguru/crud.log")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def read_poshts(db: AsyncSession = Depends(get_db)) -> Sequence[Posht]:
    result = await db.execute(select(Posht))
    poshts = result.scalars().all()
    return poshts


async def get_posht(posht_id: int, db: AsyncSession) -> Posht | None:
    result = await db.execute(select(Posht).where(Posht.id == posht_id))
    posht = result.scalar_one_or_none()
    if not posht:
        raise HTTPException(status_code=404, detail="Posht not found")
    return posht


async def create_posht(db: AsyncSession, posht: PoshtCreate, user: User) -> Posht:
    logger.info("create_posht is running 2!")
    is_blocked = await check_for_profanity(posht.posht_text)
    new_posht = Posht(
        title=posht.title,
        posht_text=posht.posht_text,
        user_id=user.id,
        is_blocked=is_blocked,
    )
    db.add(new_posht)
    await db.commit()
    await db.refresh(new_posht)
    return new_posht


async def update_posht(
    db: AsyncSession, posht_id: int, posht: PoshtUpdate
) -> Posht | None:
    logger.info("update_posht is running!")
    is_blocked = await check_for_profanity(posht.posht_text)
    result = await db.execute(select(Posht).where(Posht.id == posht_id))
    db_posht = result.scalar_one_or_none()
    if not db_posht:
        return None

    db_posht.title = posht.title
    db_posht.posht_text = posht.posht_text
    db_posht.is_blocked = is_blocked
    await db.commit()
    await db.refresh(db_posht)
    return db_posht


async def delete_posht(db: AsyncSession, posht_id: int) -> Posht | None:
    result = await db.execute(select(Posht).where(Posht.id == posht_id))
    db_posht = result.scalar_one_or_none()
    if not db_posht:
        return None
    await db.delete(db_posht)
    await db.commit()
    return db_posht


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed, role=user.role)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_users_from_db(db: AsyncSession = Depends(get_db)) -> Sequence[User]:
    logger.info("get_users_from_db is running!")
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    logger.info("get_current_user_by_email is running!")
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_by_id(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> UserRead:
    payload = decode_token(token)
    logger.info("get_current_user_by_id is running!")
    logger.info("PAYLOAD:")
    logger.info(payload)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.from_orm(db_user)


async def require_admin(
    current_user: UserRead = Depends(get_current_user_by_id),
) -> UserRead:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: admins only")
    return current_user


async def read_comments(db: AsyncSession = Depends(get_db)) -> list[Comment]:
    result = await db.execute(select(Comment))
    comments = result.scalars().all()
    return comments


async def update_comment(
    db: AsyncSession, comment_id: int, comment: CommentUpdate
) -> Comment:
    is_blocked = await check_for_profanity(comment.comment_text)
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    db_comment = result.scalar_one_or_none()
    if not db_comment:
        return None

    db_comment.comment_text = comment.comment_text
    db_comment.is_blocked = is_blocked
    await db.commit()
    await db.refresh(db_comment)
    return db_comment


async def delete_comment(db: AsyncSession, comment_id: int) -> Comment | None:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    db_comment = result.scalar_one_or_none()
    if not db_comment:
        return None
    await db.delete(db_comment)
    await db.commit()
    return db_comment


async def get_comment(comment_id: int, db: AsyncSession) -> Comment:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


async def create_comment(db: AsyncSession, comment: CommentCreate) -> Comment:
    is_blocked = await check_for_profanity(comment.comment_text)
    new_comment = Comment(**comment.dict(), is_blocked=is_blocked)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    if not is_blocked:
        logger.info(
            "asyncio.create_task(create_auto_reply(db, new_comment)) is running!"
        )
        asyncio.create_task(create_auto_reply(db, new_comment))

    return new_comment


async def create_auto_reply(db: AsyncSession, comment: Comment) -> None:
    logger.info("create_auto_reply is running!")
    posht = await db.get(Posht, comment.posht_id)
    if not posht:
        return

    posth_author = await db.get(User, posht.user_id)
    if (
        not posth_author
        or posth_author.auto_comment_delay is None
        or posth_author.auto_comment_delay < 0
    ):
        return

    await asyncio.sleep(posth_author.auto_comment_delay)

    reply_text = await create_auto_reply_text(posht.posht_text, comment.comment_text)

    auto_comment = Comment(
        posht_id=comment.posht_id,
        comment_text=reply_text,
        user_id=posht.user_id,
        auto_created=True,
    )
    db.add(auto_comment)
    await db.commit()


async def create_auto_reply_text(post_text: str, comment_text: str) -> str:
    logger.info("create_auto_reply_text is running!")

    try:
        response = model.generate_content(PROMPT_FOR_AUTO_REPLY)
        reply = response.text.strip()
        logger.info("Generated reply:", repr(reply))
        return reply
    except Exception as e:
        logger.info("Error generating auto-reply:", e)
        return "Thank you for your comment!"
