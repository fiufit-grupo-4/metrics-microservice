import logging
import json
from fastapi import APIRouter
from sqlalchemy import and_, or_
from app.definitions import BLOCK, GOOGLE_SIGNUP, NEW_TRAINING, SIGNUP
from app.models import Entry, EntryCreate, EntryUpdate
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
        user_id=entry.user_id,
        ip=entry.ip,
        country=entry.country,
        action=entry.action,
        training_id=entry.training_id,
        training_type=entry.training_type,
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
    entry = await session.get(Entry, id)
    if not entry:
        return None

    for key, value in updates.dict(exclude_unset=True).items():
        setattr(entry, key, value)

    await session.commit()
    await session.refresh(entry)

    return entry


async def delete_db_entry(id: int, session: AsyncSession):
    entry = await session.get(Entry, id)
    if not entry:
        return None

    await session.delete(entry)
    await session.commit()

    return entry


async def delete_all_db_entries(session: AsyncSession):
    result = await session.execute(select(Entry))
    entries = result.scalars().all()
    for entry in entries:
        await session.delete(entry)
    await session.commit()
    return entries


async def update_db_entry_location(user_id: str, country: str, session: AsyncSession):
    result = await session.execute(
        select(Entry).where(and_(Entry.user_id == user_id, Entry.action == SIGNUP))
    )
    entry = result.scalars().one_or_none()

    if not entry:
        return None

    setattr(entry, "country", country)

    await session.commit()
    await session.refresh(entry)

    return entry


async def delete_db_entry_by_user_and_action(
    user_id: str, action: str, session: AsyncSession
):
    result = await session.execute(
        select(Entry).where(and_(Entry.user_id == user_id, Entry.action == action))
    )
    entry = result.scalars().one_or_none()

    if not entry:
        return None

    await session.delete(entry)
    await session.commit()

    return entry


async def delete_db_entry_by_training_and_action(
    training_id: str, action: str, session: AsyncSession
):
    result = await session.execute(
        select(Entry).where(
            and_(Entry.training_id == training_id, Entry.action == action)
        )
    )
    entry = result.scalars().one_or_none()

    if not entry:
        return None

    await session.delete(entry)
    await session.commit()

    return entry


async def delete_db_all_entries_with_training_id(
    training_id: str, session: AsyncSession
):
    """
    Deletes all entries with the specified training ID
    """
    result = await session.execute(
        select(Entry).where(Entry.training_id == training_id)
    )

    entries = result.scalars().all()

    for entry in entries:
        await session.delete(entry)

    await session.commit()

    return entries
