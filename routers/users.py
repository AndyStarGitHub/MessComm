from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth_util import authenticate_user
from crud import (
    create_access_token,
    create_user,
    get_current_user_by_id,
    get_user_by_email,
    get_users_from_db,
)
from database import get_db
from loguru import logger
from schemas import UserCreate, UserRead
from security import hash_password

logger.add("loguru/users.log")

router = APIRouter()


@router.get("/users", response_model=List[UserRead], tags=["users"])
async def read_users(db: AsyncSession = Depends(get_db)) -> List[UserRead]:
    logger.info("read_users is running!")
    return await get_users_from_db(db)


@router.post("/register", response_model=UserRead, tags=["users"])
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db, user)


@router.post("/login", tags=["users"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> dict:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead, tags=["users"])
def read_me(current_user: UserRead = Depends(get_current_user_by_id)) -> UserRead:
    return current_user


@router.post("/reset_password", tags=["users"])
async def reset_password(
    email: str, new_password: str, db: AsyncSession = Depends(get_db)
) -> dict:
    db_user = await get_user_by_email(db, email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.hashed_password = hash_password(new_password)
    await db.commit()
    return {"detail": "Password updated"}
