from typing import Optional
from sqlmodel import SQLModel, Field


class EntryBase(SQLModel):
    service: str
    path: str
    url: str
    method: str
    status_code: int
    datetime: str
    response_time: float
    ip: str
    country: str
    city: str


class Entry(EntryBase, table=True):
    id: int = Field(default=None, primary_key=True)


class EntryCreate(EntryBase):
    pass


class EntryUpdate(SQLModel):
    service: Optional[str]
    path: Optional[str]
    url: Optional[str]
    method: Optional[str]
    status_code: Optional[str]
    datetime: Optional[str]
    response_time: Optional[str]
    ip: Optional[str]
    country: Optional[str]
    city: Optional[str]
