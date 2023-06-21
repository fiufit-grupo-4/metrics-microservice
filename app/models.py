from typing import Dict, Optional
from sqlmodel import SQLModel, Field


class EntryBase(SQLModel):
    service: str
    path: str
    url: str
    method: str
    status_code: int
    datetime: str
    response_time: float
    user_id: str
    ip: str
    country: str = ""
    action: str
    training_id: str = ""
    training_type: str = ""


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
    user_id: str
    ip: Optional[str]
    country: Optional[str]
    action: Optional[str]
