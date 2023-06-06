import asyncio
from fastapi import FastAPI
import sqlalchemy
import logging
from logging.config import dictConfig
from app.consumer.consumer_queue import runConsumerQueue
from .log_config import logconfig
from dotenv import load_dotenv
import os
import databases
from .feature.notes import notes_router


dictConfig(logconfig)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
logger = logging.getLogger('app')
database = databases.Database(DATABASE_URL)


@app.on_event("startup")
async def startup():
    try:
        app.task_publisher_manager = asyncio.create_task(runConsumerQueue())
        await database.connect()
        metadata = sqlalchemy.MetaData()

        notes = sqlalchemy.Table(
            "notes",
            metadata,
            sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column("text", sqlalchemy.String),
            sqlalchemy.Column("completed", sqlalchemy.Boolean),
        )

        engine = sqlalchemy.create_engine(DATABASE_URL)
        metadata.create_all(engine)

        app.logger = logger
        app.database = database
        app.notes_table = notes

    except Exception as e:
        logger.error(e)
        logger.error("Could not connect to Postgres")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    app.task_publisher_manager.cancel()
    app.consumer.stop()
    logger.info("Shutdown APP")


app.include_router(
    notes_router,
    prefix="/notes",
    tags=["Notes - Metrics Microservice"],
)
