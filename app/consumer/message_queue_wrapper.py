import json
from app.entries_utils import (
    add_db_entry,
    delete_db_all_entries_with_training_id,
    delete_db_entry_by_training_and_action,
    delete_db_entry_by_user_and_action,
    update_db_entry_location,
)
import app.main as main
from app.db import get_session
from app.definitions import (
    ADD_TRAINING_TO_FAVS,
    BLOCK,
    DELETE_TRAINING,
    MEDIA_UPLOAD,
    NEW_TRAINING,
    REMOVE_TRAINING_FROM_FAVS,
    TRAINING_SERVICE,
    USER_EDIT,
    UNBLOCK,
    USER_SERVICE,
)
from app.models import EntryCreate


async def MessageQueueWrapper(channel, basic_deliver, properties, message):
    """
    Wrapper de la funcion "ConsumerQueue.on_message()"

    :param pika.channel.Channel channel: The channel object
    :param pika.Spec.Basic.Deliver: basic_deliver method
    :param pika.Spec.BasicProperties: properties
    :param bytes body: The message body
    """
    message = json.loads(message.decode('utf-8'))
    main.logger.info(message)

    async for session in get_session():
        service = message.get("service")
        country = message.get("country")
        user_id = message.get("user_id")
        action = message.get("action")

        main.logger.info(f"[QUEUE] New message received from {service}")

        if service == USER_SERVICE:
            if action == UNBLOCK:
                await delete_db_entry_by_user_and_action(user_id, BLOCK, session)
            elif action == USER_EDIT and country:
                await update_db_entry_location(user_id, country, session)
            elif action == REMOVE_TRAINING_FROM_FAVS:
                training_id = message.get("training_id")
                await delete_db_entry_by_training_and_action(
                    training_id, ADD_TRAINING_TO_FAVS, session
                )
            else:
                await add_db_entry(EntryCreate(**message), session)

        if service == TRAINING_SERVICE:
            if action in (NEW_TRAINING, MEDIA_UPLOAD):
                await add_db_entry(EntryCreate(**message), session)
            elif action == DELETE_TRAINING:
                training_id = message.get("training_id")
                await delete_db_all_entries_with_training_id(training_id, session)
