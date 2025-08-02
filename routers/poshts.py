from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from schemas import (PoshtCreate,
                     PoshtRead,
                     PoshtUpdate
                    )
from database import get_db
from crud import (read_poshts as get_poshts_from_db,
                  delete_posht,
                  get_current_user_by_id,
                  require_admin
                  )
from crud import get_posht as get_posht_from_db
from crud import update_posht as update_posht_from_db
from crud import create_posht as create_posht_from_db

router = APIRouter(prefix="/poshts", tags=["poshts"])


@router.get("/", response_model=List[PoshtRead], tags=["poshts"])
async def get_poshts(
        db: AsyncSession = Depends(get_db)
) -> List[PoshtRead]:
    return await get_poshts_from_db(db)


@router.get("/{posht_id}", response_model=PoshtRead, tags=["poshts"])
async def get_posht(posht_id: int,
                    db: AsyncSession = Depends(get_db)
                    ) -> PoshtRead:
    return await get_posht_from_db(posht_id, db)


@router.post("/", response_model=PoshtRead, tags=["poshts"])
async def create_posht(
        posht: PoshtCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user_by_id),
        ) -> PoshtRead:
    new_posht = await create_posht_from_db(db, posht, current_user)
    return new_posht


@router.put("/{posht_id}", response_model=PoshtRead)
async def update_posht(
    posht_id: int,
    posht: PoshtUpdate,
    db: AsyncSession = Depends(get_db)
) -> PoshtRead:
    updated_posht = await update_posht_from_db(db, posht_id, posht)
    if not updated_posht:
        raise HTTPException(status_code=404, detail="Posht not found")
    return updated_posht


@router.delete(
    "/{posht_id}",
    response_model=PoshtRead,
    dependencies=[Depends(require_admin)]
)
async def remove_posht(
        posht_id: int,
        db: AsyncSession = Depends(get_db)
) -> PoshtRead:
    deleted_posht = await delete_posht(db, posht_id)
    if not deleted_posht:
        raise HTTPException(status_code=404, detail="Posht not found")
    return deleted_posht
