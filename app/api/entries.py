import logging
from fastapi import APIRouter, Depends, status
from app.db import get_session
from app.models import Entry, EntryCreate, EntryUpdate
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from app.entries_utils import (
    add_db_entry,
    delete_all_db_entries,
    delete_db_entry,
    get_db_entries,
    get_db_entry_by_id,
    update_db_entry,
)

# https://fastapi.tiangolo.com/advanced/async-sql-databases/ 😎

entries_router = APIRouter()
logger = logging.getLogger('app')


@entries_router.post("/")
async def add_entry(entry: EntryCreate, session: AsyncSession = Depends(get_session)):
    entry_obj = await add_db_entry(entry, session)
    return entry_obj


@entries_router.get("/{id}", response_model=Entry)
async def get_entry(id: int, session: AsyncSession = Depends(get_session)):
    entry = await get_db_entry_by_id(id=id, session=session)
    return entry


@entries_router.get("/", response_model=list[Entry])
async def get_entries(session: AsyncSession = Depends(get_session)):
    entries = await get_db_entries(session=session)
    return entries


@entries_router.put("/{id}")
async def update_entry(
    id: int, updates: EntryUpdate, session: AsyncSession = Depends(get_session)
):
    entry = await update_db_entry(id, updates, session)
    if not entry:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Entry {id} not found",
        )
    return entry


@entries_router.delete("/{id}")
async def delete_entry(id: int, session: AsyncSession = Depends(get_session)):
    response = await delete_db_entry(id, session)
    if not response:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Entry {id} not found",
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=f"Entry {id} deleted",
    )


@entries_router.delete("/")
async def delete_entries(session: AsyncSession = Depends(get_session)):
    entries = await delete_all_db_entries(session)
    if not entries:
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content="No entries to delete",
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content="All entries have been deleted successfully",
    )
