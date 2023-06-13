import logging
from fastapi import APIRouter
from app.models import Entry, EntryCreate, EntryUpdate
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# https://fastapi.tiangolo.com/advanced/async-sql-databases/ 😎

entries_router = APIRouter()
logger = logging.getLogger('app')


async def add_db_entry(entry: EntryCreate, session: AsyncSession):
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


async def get_db_entry_by_id(id: int, session: AsyncSession):
    result = await session.execute(select(Entry).where(Entry.id == id))
    entry = result.scalars().first()
    return Entry.from_orm(entry)


async def get_db_entries(session: AsyncSession):
    result = await session.execute(select(Entry))
    entries = result.scalars().all()
    return [entry for entry in entries]


async def update_db_entry(id: int, updates: EntryUpdate, session: AsyncSession):
    item = await session.get(Entry, id)
    if not item:
        return None

    for key, value in updates.dict(exclude_unset=True).items():
        setattr(item, key, value)

    await session.commit()
    await session.refresh(item)

    return item


async def delete_db_entry(id: int, session: AsyncSession):
    item = await session.get(Entry, id)
    if not item:
        None

    await session.delete(item)
    await session.commit()

    return item


async def delete_all_db_entries(session: AsyncSession):
    result = await session.execute(select(Entry))
    entries = result.scalars().all()
    for entry in entries:
        await session.delete(entry)
    await session.commit()
    return entries
