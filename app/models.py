from sqlmodel import SQLModel, Field


class EntryBase(SQLModel):
    timestamp: str
    service_name: str
    http_method: str
    status_code: int


class Entry(EntryBase, table=True):
    id: int = Field(default=None, primary_key=True)


class EntryCreate(EntryBase):
    pass