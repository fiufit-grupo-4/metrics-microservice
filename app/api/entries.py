import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.db import get_session
from app.models import Entry, EntryCreate
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger('app')
entries_router = APIRouter()

# https://fastapi.tiangolo.com/advanced/async-sql-databases/ 😎


@entries_router.post("/entries")
async def add_entry(entry: EntryCreate, session: AsyncSession = Depends(get_session)):
    entry = Entry(
        service = entry.service,
        path = entry.path,
        url = entry.url,
        method = entry.method,
        status_code = entry.status_code,
        datetime = entry.datetime,
        response_time = entry.response_time,
        ip = entry.ip,
        country = entry.country,
        city = entry.city,
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
        service = entry.service,
        path = entry.path,
        url = entry.url,
        method = entry.method,
        status_code = entry.status_code,
        datetime = entry.datetime,
        response_time = entry.response_time,
        ip = entry.ip,
        country = entry.country,
        city = entry.city,
    )


@entries_router.get("/entries", response_model=list[Entry])
async def get_entries(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Entry))
    entries = result.scalars().all()
    return [
        Entry(
            id=entry.id,
        service = entry.service,
        path = entry.path,
        url = entry.url,
        method = entry.method,
        status_code = entry.status_code,
        datetime = entry.datetime,
        response_time = entry.response_time,
        ip = entry.ip,
        country = entry.country,
        city = entry.city,
        )
        for entry in entries
    ]
