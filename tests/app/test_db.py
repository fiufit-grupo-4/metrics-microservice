import os

class SQLModel:
    metadata = "mock_metadata"

class AsyncSession:
    def __init__(self):
        self.session = "mock_session"
    
    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class SessionMaker:
    def __init__(self):
        self.engine = "mock_engine"
        
    def __call__(self, *args, **kwargs):
        return AsyncSession()

os.environ = {}

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = "mock_engine"


async def init_db():
    async with "mock_connection" as conn:
        pass


async def get_session() -> AsyncSession:
    return AsyncSession()
