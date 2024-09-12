from typing import AsyncIterator
from dotenv import find_dotenv, load_dotenv
import logging, asyncio, json
from fastapi import FastAPI
from colorama import Fore
from redis import Redis
from confluent_kafka import Consumer
from contextlib import asynccontextmanager
import os
import datetime
from routes import token_routes

logging.basicConfig(level=logging.INFO, format=f'{Fore.MAGENTA}[API]{Fore.RESET} %(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
load_dotenv(find_dotenv(".env"))

api_host = os.getenv("API_HOST")
api_port = os.getenv("API_PORT") 

redis_port = os.getenv("REDIS_PORT")
token_stale_channel = os.getenv("REDIS_STALE_CHANNEL")

kafka_remote = os.getenv("KAFKA_BROKER")
kafka_port = os.getenv("KAFKA_PORT")

redis = Redis(host=str(os.getenv("REDIS_HOST")), port=int(redis_port), db=0) #type: ignore

interested_topics = [
    os.getenv("KAFKA_PRICES_TOPIC"),
    os.getenv("KAFKA_VOLUMES_TOPIC"),
    os.getenv("KAFKA_TOP_HOLDERS_TOPIC"),
    os.getenv("KAFKA_BURNS_TOPIC"),
    os.getenv("KAFKA_TOKENS_TOPIC"),
]

if not api_port:
    logging.error("API_PORT not found in .env")
    exit(1)

if not redis_port:
    logging.error("REDIS_PORT not found in .env")
    exit(1)

if not token_stale_channel:
    logging.error("REDIS_TOKEN_STALE_CHANNEL not found in .env")
    exit(1)

async def listen_to_all_topics():
    try:
        consumer = Consumer({
            'bootstrap.servers': f"{kafka_remote}:{kafka_port}",
            'group.id': 'events-api',
            'auto.offset.reset': 'earliest'
        })
        return consumer
    
    except Exception as e:
        logging.error(f"Error in Kafka consumer: {e}")
        exit(1)

async def pub_to_timescale(data: dict):
    pass

async def kafka_listener():
    # kafka consumer task
    consumer = await listen_to_all_topics()
    consumer.subscribe(interested_topics)
    logging.info("Subscribed to topics")

    while True:
        message = consumer.poll(timeout=1.0)

        if message is None:
            continue
        if message.error():
            logging.error(f"Consumer error: {message.error()}")
            continue

        topic = message.topic()
        key = message.key()
        value = message.value()
        timestamp = datetime.datetime.fromtimestamp(message.timestamp()[1] / 1e3)

        logging.info(f"Received message: {topic} {key} {value} {timestamp}")


@asynccontextmanager
async def start_kafka_listener(application: FastAPI):
    asyncio.create_task(kafka_listener())  # This will run kafka_listener as a background task
    yield
    logging.info("Stopping Kafka listener")

app = FastAPI(lifespan=start_kafka_listener)
app.include_router(token_routes.router, prefix="/api", tags=["tokens"])


if __name__ == "__main__":
    import uvicorn 
    try:
        logging.info("Starting Kafka listener")

        logging.info("Starting API")
        uvicorn.run(app, host=api_host, port=int(api_port))  # Run the app directly without asyncio.run()
    except Exception as e:
        logging.error(f"Error in main: {e}")
        exit(1)
