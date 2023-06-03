import asyncio
from fastapi import FastAPI
from app.controller_example import router as example_router
import logging
from logging.config import dictConfig

from app.consumer.consumer_queue import runConsumerQueue
from .log_config import logconfig
from os import environ
import os

# MONGODB_URI = environ["MONGODB_URI"]

dictConfig(logconfig)
app = FastAPI()
logger = logging.getLogger('app')


@app.on_event("startup")
async def startup_db_client():
    app.task_publisher_manager = asyncio.create_task(runConsumerQueue())
    # try:
    #     app.mongodb_client = pymongo.MongoClient(MONGODB_URI)
    #     logger.info("Connected successfully MongoDB")

    # except Exception as e:
    #     logger.error(e)
    #     logger.error("Could not connect to MongoDB")

    # How to build a collection
    # db = app.mongodb_client["example-db"]
    # collection = db.example_collection

    # collection.delete_many({})  # Clear collection data
    
    logger.info("Startup APP!")


@app.on_event("shutdown")
async def shutdown_db_client():
    app.task_publisher_manager.cancel()
    app.consumer.stop()
    logger.info("Shutdown APP")


app.include_router(example_router)
