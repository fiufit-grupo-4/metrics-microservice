import asyncio
import logging
from logging.config import dictConfig
from fastapi import FastAPI
from app.consumer.consumer_queue import runConsumerQueue
from .log_config import logconfig
from dotenv import load_dotenv
from app.db import init_db
from app.api.entries import entries_router


dictConfig(logconfig)
load_dotenv()


app = FastAPI()
logger = logging.getLogger('app')


@app.on_event("startup")
async def on_startup():
    try:
        app.task_publisher_manager = asyncio.create_task(runConsumerQueue())
        await init_db()
        app.logger = logger
    except Exception as e:
        logger.error(e)
        logger.error("Could not connect to Postgres")


app.include_router(
    entries_router,
    prefix="/entries",
    tags=["Entries - Metrics Microservice"],
)
