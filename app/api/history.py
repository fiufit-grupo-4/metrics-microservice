import logging
from fastapi import APIRouter, Depends, status
from app.db import get_session
from app.definitions import (
    ADD_TRAINING_TO_FAVS,
    MEDIA_UPLOAD,
    NEW_TRAINING,
    SIGNUP,
    TRAINING_SERVICE,
    USER_SERVICE,
)
from app.models import Entry, EntryCreate, EntryUpdate
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from collections import Counter

# https://fastapi.tiangolo.com/advanced/async-sql-databases/ 😎

history_router = APIRouter()


@history_router.get("/users_auth", response_model=dict)
async def get_users_auth_requests_count(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the number of requests per auth requests
    """
    paths = (
        "/login/",
        "/login/google/",
        "/signup/",
        "/signup/google/",
        "/login/forgot_password",
    )

    counts_query = (
        select(func.count(), Entry.path)
        .where(Entry.service == USER_SERVICE)
        .where(Entry.path.in_(paths))
        .group_by(Entry.path)
    )

    counts_result = await session.execute(counts_query)

    counts = {path[1]: path[0] for path in counts_result}

    return counts


@history_router.get("/blocked_users", response_model=dict)
async def get_blocked_users_count(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the number of blocked users per YYYY-MM
    """
    path = "/users/{user_id}/block"

    counts_query = (
        select(func.count(), func.substr(Entry.datetime, 0, 8))
        .where(Entry.service == USER_SERVICE)
        .where(Entry.path.like(path.replace("{user_id}", "%")))
        .group_by(func.substr(Entry.datetime, 0, 8), Entry.datetime)
    )

    counts_result = await session.execute(counts_query)

    counts = dict(Counter(date for _, date in counts_result))

    return counts


@history_router.get("/users_by_location", response_model=dict)
async def get_users_by_location(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the number of users per country.
    Empty string ("") indicates unknown locations.
    """

    counts_query = (
        select(func.count(), Entry.country)
        .where(Entry.service == USER_SERVICE)
        .where(Entry.action == SIGNUP)
        .group_by(Entry.country)
    )

    counts_result = await session.execute(counts_query)

    counts = {country: count for count, country in counts_result}

    return counts


@history_router.get("/trainings_requests_count", response_model=dict)
async def get_trainings_requests_count(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the count of each training action
    """
    actions = ("new_training", "media_upload")

    counts_query = (
        select(func.count(), Entry.action)
        .where(Entry.service == TRAINING_SERVICE)
        .where(Entry.action.in_(actions))
        .group_by(Entry.action)
    )

    counts_result = await session.execute(counts_query)

    counts = {action[1]: action[0] for action in counts_result}

    return counts


@history_router.get("/new_trainings_per_month", response_model=dict)
async def get_new_trainings_per_month(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the number of new trainings per YYYY-MM
    """

    counts_query = (
        select(func.count(), func.substr(Entry.datetime, 0, 8))
        .where(Entry.service == TRAINING_SERVICE)
        .where(Entry.action == NEW_TRAINING)
        .group_by(func.substr(Entry.datetime, 0, 8), Entry.datetime)
    )

    counts_result = await session.execute(counts_query)

    counts = dict(Counter(date for _, date in counts_result))

    return counts


@history_router.get("/trainings_uploads_by_user", response_model=dict)
async def get_trainings_uploads_by_user(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the number of trainings uploads by user
    """

    counts_query = (
        select(func.count(), Entry.user_id)
        .where(Entry.service == TRAINING_SERVICE)
        .where(Entry.action == MEDIA_UPLOAD)
        .group_by(Entry.user_id)
    )

    counts_result = await session.execute(counts_query)

    counts = {user[1]: user[0] for user in counts_result}

    return counts


@history_router.get("/trainings_per_type", response_model=dict)
async def get_trainings_per_type(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the number of trainings per type
    """

    counts_query = (
        select(func.count(), Entry.training_type)
        .where(Entry.service == TRAINING_SERVICE)
        .where(Entry.action == NEW_TRAINING)
        .group_by(Entry.training_type)
    )

    counts_result = await session.execute(counts_query)

    counts = {training_type[1]: training_type[0] for training_type in counts_result}

    return counts


@history_router.get("/favorite_trainings_per_location", response_model=dict)
async def get_favorite_trainings_per_location(
    session: AsyncSession = Depends(get_session),
):
    """
    Returns a dict with the number of favourite trainings per location.
    Empty string ("") indicates unknown locations.
    """

    counts_query = (
        select(func.count(), Entry.country)
        .where(Entry.service == USER_SERVICE)
        .where(Entry.action == ADD_TRAINING_TO_FAVS)
        .group_by(Entry.country)
    )

    counts_result = await session.execute(counts_query)
    counts = {}
    for user in counts_result:
        counts[user["country"]] = user["count"]

    return counts


@history_router.get("/favorite_trainings_by_user", response_model=dict)
async def get_favorite_trainings_by_user(session: AsyncSession = Depends(get_session)):
    """
    Returns a dict with the number of favorite trainings by user
    """

    counts_query = (
        select(func.count(), Entry.user_id)
        .where(Entry.service == USER_SERVICE)
        .where(Entry.action == ADD_TRAINING_TO_FAVS)
        .group_by(Entry.user_id)
    )

    counts_result = await session.execute(counts_query)
    counts = {user["user_id"]: user["count"] for user in counts_result}

    return counts
