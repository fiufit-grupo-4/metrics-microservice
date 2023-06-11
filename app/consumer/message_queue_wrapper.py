import json
from fastapi import Request, Response
import app.main as main
from app.db import get_session
from app.models import EntryCreate, Entry


async def MessageQueueWrapper(channel, basic_deliver, properties, message):
    """
    Wrapper de la funcion "ConsumerQueue.on_message()"

    :param pika.channel.Channel channel: The channel object
    :param pika.Spec.Basic.Deliver: basic_deliver method
    :param pika.Spec.BasicProperties: properties
    :param bytes body: The message body
    """
    message = json.loads(message.decode('utf-8'))

    async for session in get_session():
        entry = EntryCreate(**message)
        entry_dict = entry.dict()
        db_entry = Entry(**entry_dict)
        session.add(db_entry)
        await session.commit()
        await session.refresh(db_entry)
        main.logger.info(f"Entry {db_entry.id} added to database")
