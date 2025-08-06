from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud import create_comment as create_comment_from_db
from crud import delete_comment
from crud import get_comment as get_comment_from_db
from crud import read_comments as get_comments_from_db
from crud import require_admin
from crud import update_comment as update_comment_from_db
from database import get_db
from schemas import CommentCreate, CommentRead, CommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/", response_model=List[CommentRead], tags=["comments"])
async def get_comments(db: AsyncSession = Depends(get_db)) -> CommentRead:
    return await get_comments_from_db(db)


@router.get("/{comment_id}", response_model=CommentRead, tags=["comments"])
async def get_comment(
    comment_id: int, db: AsyncSession = Depends(get_db)
) -> CommentRead:
    return await get_comment_from_db(comment_id, db)


@router.post("/", response_model=CommentRead, tags=["comments"])
async def create_comment(
    comment: CommentCreate, db: AsyncSession = Depends(get_db)
) -> CommentRead:
    new_comment = await create_comment_from_db(db, comment)
    return new_comment


@router.put("/{comment_id}", response_model=CommentRead)
async def update_comment(
    comment_id: int, comment: CommentUpdate, db: AsyncSession = Depends(get_db)
) -> CommentRead:
    updated_comment = await update_comment_from_db(db, comment_id, comment)
    if not updated_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return updated_comment


@router.delete(
    "/{comment_id}", response_model=CommentRead, dependencies=[Depends(require_admin)]
)
async def remove_comment(
    comment_id: int, db: AsyncSession = Depends(get_db)
) -> CommentRead:
    deleted_comment = await delete_comment(db, comment_id)
    if not deleted_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return deleted_comment
