import pytest
import databases
import pytest_asyncio
import sqlalchemy
from sqlalchemy.util import deprecations
from unittest.mock import MagicMock, patch
from app.models import EntryCreate, Entry, EntryUpdate
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from app.entries_utils import add_db_entry, delete_all_db_entries, delete_db_all_entries_with_training_id, delete_db_entry, delete_db_entry_by_training_and_action, get_db_entries, get_db_entry_by_id, update_db_entry, update_db_entry_location

deprecations.SILENCE_UBER_WARNING = True


entry_1_dict = {
    "service": "example1",
    "path": "/example1",
    "url": "http://example1.com",
    "method": "GET",
    "status_code": 200,
    "datetime": "2021-12-01 12:34:56",
    "response_time": 0.123,
    "user_id": "1a2b3c",
    "ip": "192.168.0.1",
    "country": "China",
    "action": "login",
    "training_id": "4d5e6f",
    "training_type": "test"
}

entry_2_dict = {
    "service": "example2",
    "path": "/example2",
    "url": "http://example2.com",
    "method": "POST",
    "status_code": 200,
    "datetime": "2021-12-01 12:34:56",
    "response_time": 0.123,
    "user_id": "1a2b3c",
    "ip": "192.168.0.1",
    "country": "USA",
    "action": "login",
    "training_id": "4d5e6f",
    "training_type": "test"
}

class MockAsyncSession:
    def __init__(self):
        self.added_objects = []
        self.committed = False

    async def get(self, entity, ident):
        return self.added_objects[0]

    async def add(self, obj):
        self.added_objects.append(obj)

    async def delete(self, entry):
        self.added_objects.pop()

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass

    async def execute(self, obj):
        pass


@pytest_asyncio.fixture
async def async_db_engine():
    # Create a local PostgreSQL database for testing
    db_url = "postgresql+asyncpg://smcihhmivkhfyy:5eea3139185bcb8f9097956e342d8c5da2ca65eea490657136eef2f4a0520285@ec2-3-234-204-26.compute-1.amazonaws.com:5432/dfh6irv28ooujc"

    database = databases.Database(db_url)

    metadata = sqlalchemy.MetaData()

    entries_table = sqlalchemy.Table(
        "entries-test",
        metadata,
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column("service", sqlalchemy.String),
        sqlalchemy.Column("path", sqlalchemy.String),
        sqlalchemy.Column("url", sqlalchemy.String),
        sqlalchemy.Column("method", sqlalchemy.String),
        sqlalchemy.Column("status_code", sqlalchemy.Integer),
        sqlalchemy.Column("datetime", sqlalchemy.String),
        sqlalchemy.Column("response_time", sqlalchemy.Float),
        sqlalchemy.Column("user_id", sqlalchemy.String),
        sqlalchemy.Column("ip", sqlalchemy.String),
        sqlalchemy.Column("country", sqlalchemy.String),
        sqlalchemy.Column("action", sqlalchemy.String),
        sqlalchemy.Column("training_id", sqlalchemy.String),
        sqlalchemy.Column("training_type", sqlalchemy.String)
    )
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        Base = declarative_base()
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
@pytest.hookimpl(optionalhook=True)
async def test_add_db_entry(async_db_engine):
    session = MockAsyncSession()

    entry = EntryCreate(**entry_1_dict)

    result = await add_db_entry(entry, session)

    entry_1_dict["id"] = None

    assert session.committed
    assert result == Entry(**entry_1_dict)


@pytest.mark.asyncio
async def test_delete_db_entry(async_db_engine):
    session = MockAsyncSession()

    entry_1_dict["id"] = "1a2b3c"
    entry = Entry(**entry_1_dict)
    
    await session.add(entry)

    result = await delete_db_entry("1a2b3c", session)

    assert len(session.added_objects) == 0
    assert result == entry


@pytest.mark.asyncio
async def test_delete_all_db_entries(async_db_engine):
    session = MockAsyncSession()

    entry_1_dict["id"] = "1a2b3c"
    entry_2_dict["id"] = "4d5e6f"
    entry_1 = Entry(**entry_1_dict)
    entry_2 = Entry(**entry_2_dict)
    
    await session.add(entry_1)
    await session.add(entry_2)

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [entry_1, entry_2]
    scalars_mock = MagicMock(return_value=result_mock)
    
    with patch.object(session, 'execute', return_value=result_mock):
        result = await delete_all_db_entries(session)
        assert len(session.added_objects) == 0

    assert session.committed


@pytest.mark.asyncio
async def test_update_db_entry(async_db_engine):
    session = MockAsyncSession()

    entry_1_dict["id"] = "4d5e6f"
    entry = Entry(**entry_1_dict)
    updates_dict = {
        "user_id": "123456",
        "country": "Chile"
    }
    updates = EntryUpdate(**updates_dict)

    with patch.object(session, 'get', return_value=entry) as get_mock:
        result = await update_db_entry("4d5e6f", updates, session)
        get_mock.assert_called_once_with(Entry, "4d5e6f")
        
        assert session.committed
        assert result == entry
        assert entry.user_id == updates.user_id
        assert entry.country == updates.country


@pytest.mark.asyncio
async def test_get_db_entries(async_db_engine):
    session = MockAsyncSession()

    entry_1_dict["id"] = "1a2b3c"
    entry_2_dict["id"] = "4d5e6f"
    entry_1 = Entry(**entry_1_dict)
    entry_2 = Entry(**entry_2_dict)
    
    await session.add(entry_1)
    await session.add(entry_2)

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [entry_1, entry_2]
    scalars_mock = MagicMock(return_value=result_mock)
    
    with patch.object(session, 'execute', return_value=result_mock):
        result = await get_db_entries(session)
        assert len(result) == 2


@pytest.mark.asyncio
async def test_get_db_entry_by_id(async_db_engine):
    session = MockAsyncSession()

    entry_1_dict["id"] = "1a2b3c"
    entry_1 = Entry(**entry_1_dict)
    
    await session.add(entry_1)

    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = entry_1
    scalars_mock = MagicMock(return_value=result_mock)
    
    with patch.object(session, 'execute', return_value=result_mock):
        result = await get_db_entry_by_id("1a2b3c", session)
        assert result.user_id == "1a2b3c"


@pytest.mark.asyncio
async def test_update_db_entry_location(async_db_engine):
    session = MockAsyncSession()

    user_id = "1a2b3c"
    country = "Canada"

    entry_1_dict["id"] = "4d5e6f"
    entry_1_dict["user_id"] = user_id
    entry = Entry(**entry_1_dict)

    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = entry
    scalars_mock = MagicMock(return_value=result_mock)

    with patch.object(session, 'execute', return_value=result_mock):
        result = await update_db_entry_location(user_id, country, session)
        session.committed
        session.execute.assert_called_once

        assert result == entry
        assert entry.country == country


@pytest.mark.asyncio
async def test_delete_db_all_entries_with_training_id(async_db_engine):
    session = MockAsyncSession()

    training_id = "4d5e6f"

    entry_1_dict["id"] = "1a2b3c"
    entry_1_dict["training_id"] = training_id
    entry_1 = Entry(**entry_1_dict)

    entry_2_dict["id"] = "7g8h9i"
    entry_2_dict["training_id"] = training_id
    entry_2 = Entry(**entry_2_dict)

    await session.add(entry_1)
    await session.add(entry_2)

    entries = [entry_1, entry_2]

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = entries
    scalars_mock = MagicMock(return_value=result_mock)

    with patch.object(session, 'execute', return_value=result_mock):
        result = await delete_db_all_entries_with_training_id(training_id, session)
        session.execute.assert_called_once
        session.committed

        assert result == entries


@pytest.mark.asyncio
async def test_delete_db_entry_by_training_and_action(async_db_engine):
    session = MockAsyncSession()

    training_id = "4d5e6f"
    action = "login"

    entry_1_dict["id"] = "1a2b3c"
    entry_1_dict["training_id"] = training_id

    entry = Entry(**entry_1_dict)
    await session.add(entry)

    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = entry
    scalars_mock = MagicMock(return_value=result_mock)

    with patch.object(session, 'execute', return_value=result_mock):
        result = await delete_db_entry_by_training_and_action(training_id, action, session)
        session.execute.assert_called_once
        session.committed

        assert result == entry
        assert len(session.added_objects) == 0


