import logging
from typing import List
from fastapi import APIRouter, Depends, status
from app.db import get_session
from app.models import Entry, EntryCreate, EntryUpdate
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

logger = logging.getLogger('app')
entries_router = APIRouter()


# https://fastapi.tiangolo.com/advanced/async-sql-databases/ 😎


@entries_router.post("/entries")
async def add_entry(entry: EntryCreate, session: AsyncSession = Depends(get_session)):
    entry = Entry(
        service=entry.service,
        path=entry.path,
        url=entry.url,
        method=entry.method,
        status_code=entry.status_code,
        datetime=entry.datetime,
        response_time=entry.response_time,
        ip=entry.ip,
        country=entry.country,
        city=entry.city,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@entries_router.get("/entries/{id}", response_model=Entry)
async def get_entry(id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Entry).where(Entry.id == id))
    entry = result.scalars().first()
    return Entry(
        id=entry.id,
        service=entry.service,
        path=entry.path,
        url=entry.url,
        method=entry.method,
        status_code=entry.status_code,
        datetime=entry.datetime,
        response_time=entry.response_time,
        ip=entry.ip,
        country=entry.country,
        city=entry.city,
    )


@entries_router.get("/entries", response_model=list[Entry])
async def get_entries(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Entry))
    entries = result.scalars().all()
    return [
        Entry(
            id=entry.id,
            service=entry.service,
            path=entry.path,
            url=entry.url,
            method=entry.method,
            status_code=entry.status_code,
            datetime=entry.datetime,
            response_time=entry.response_time,
            ip=entry.ip,
            country=entry.country,
            city=entry.city,
        )
        for entry in entries
    ]


@entries_router.put("/entries/{id}")
async def update_entry(
    id: int, updates: EntryUpdate, session: AsyncSession = Depends(get_session)
):
    item = await session.get(Entry, id)
    logging.critical("item: %s", item)
    if not item:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Entry {id} not found',
        )

    for key, value in updates.dict(exclude_unset=True).items():
        setattr(item, key, value)

    # Commit the changes
    await session.commit()

    # Refresh the item object to reflect the updated values
    await session.refresh(item)

    return item


@entries_router.delete("/entries/{id}")
async def delete_entry(id: int, session: AsyncSession = Depends(get_session)):
    item = await session.get(Entry, id)
    if not item:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Entry {id} not found',
        )

    await session.delete(item)
    await session.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=f'Entry {id} deleted',
    )


@entries_router.delete("/entries")
async def delete_all(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Entry))
    entries = result.scalars().all()
    for entry in entries:
        await session.delete(entry)
    await session.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content='All entries deleted',
    )
