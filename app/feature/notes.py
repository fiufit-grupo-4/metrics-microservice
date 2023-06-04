import logging
from typing import List
from fastapi import APIRouter, Request
from .models import Note, NoteIn


logger = logging.getLogger('app')
notes_router = APIRouter()

# https://fastapi.tiangolo.com/advanced/async-sql-databases/ 😎

@notes_router.get("/", response_model=List[Note])
async def read_notes(request: Request):
    query = request.app.notes_table.select()
    return await request.database.fetch_all(query)


@notes_router.post("/", response_model=Note)
async def create_note(request: Request, note: NoteIn):
    query = request.app.notes_table.insert().values(text=note.text, completed=note.completed)
    last_record_id = await request.database.execute(query)
    return {**note.dict(), "id": last_record_id}