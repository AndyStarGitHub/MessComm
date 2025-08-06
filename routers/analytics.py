from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from loguru import logger
from models import Comment

logger.add("loguru/alanytics.log")

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/comments/")
async def get_comments_analytics(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    logger.info("🔥 get_comments_analytics is running!")

    query = (
        select(
            func.date(Comment.created_at).label("date"),
            func.count().label("count"),
            func.sum(case((Comment.is_blocked.is_(True), 1), else_=0)).label(
                "blocked_count"
            ),
        )
        .group_by(func.date(Comment.created_at))
        .order_by(func.date(Comment.created_at))
    )

    result = await db.execute(query)
    analytics = [
        {"date": str(row.date), "count": row.count, "blocked_count": row.blocked_count}
        for row in result.fetchall()
    ]

    return analytics
