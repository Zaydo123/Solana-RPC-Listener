# app.include_router(token_routes.router, prefix="/api", tags=["tokens"])
import uvicorn
from dotenv import find_dotenv, load_dotenv
import logging, asyncio, json
from fastapi import FastAPI
from colorama import Fore
from redis import Redis
from confluent_kafka import Consumer, KafkaError, KafkaException
from contextlib import asynccontextmanager
import os, sys, socket
import datetime
# from routes import token_routes

logging.basicConfig(level=logging.INFO, format=f'{Fore.MAGENTA}[API]{Fore.RESET} %(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# - - - - - CONFIG - - - - -

load_dotenv(find_dotenv(".env"))
api_host = os.getenv("API_HOST")
api_port = os.getenv("API_PORT") 
redis_port = os.getenv("REDIS_PORT")
kafka_remote = os.getenv("KAFKA_BROKER")
kafka_port = os.getenv("KAFKA_PORT")

interested_topics = [
    os.getenv("KAFKA_PRICES_TOPIC"),
    os.getenv("KAFKA_VOLUMES_TOPIC"),
    os.getenv("KAFKA_TOP_HOLDERS_TOPIC"),
    os.getenv("KAFKA_BURNS_TOPIC"),
    os.getenv("KAFKA_TOKENS_TOPIC"),
]

event_types = {
    "prices": os.getenv("KAFKA_PRICES_TOPIC"),
    "volumes": os.getenv("KAFKA_VOLUMES_TOPIC"),
    "top_holders": os.getenv("KAFKA_TOP_HOLDERS_TOPIC"),
    "burns": os.getenv("KAFKA_BURNS_TOPIC"),
    "tokens": os.getenv("KAFKA_TOKENS_TOPIC"),
}

#any none true if any intersted topics are none
any_none = any([not i for i in interested_topics])
terminate = True if any_none else False
# terminate if any of the other environment variables are missing
terminate=True if not all([api_host, api_port, redis_port, kafka_remote, kafka_port, ]) else False
logging.error("Missing environment variables") if terminate else None
sys.exit(1) if terminate else None

# - - - - - END CONFIG - - - - -

term_deadline_timestamp = None
consumer = None
redis = Redis(host=str(os.getenv("REDIS_HOST")), port=int(redis_port), db=0) #type: ignore

async def pub_to_timescale(data: dict):
    logging.info(f"Publishing to Timescale: {data}")


async def commit_callback(err, partitions):
    if err:
        logging.error(f"Commit error: {err}")
    else:
        logging.info(f"Committed: {partitions}")

async def kafka_listener():
    global consumer

    try:
        logging.info(f"Connecting to Kafka: {kafka_remote}:{kafka_port}")
        consumer = Consumer(
            {
                'bootstrap.servers': kafka_remote,
                'group.id': 'logger-api',
                'session.timeout.ms': 6000,
                'on_commit': commit_callback,
                'auto.offset.reset': 'earliest'
            }
        )

    except KafkaError as e:
        logging.error(f"KafkaError -> : {e}")
        exit(1)
    except Exception as e:
        logging.error(f"Error in Kafka consumer: {e}")
        exit(1)

    if not consumer:
        logging.error("Consumer not created")
        exit(1)
    consumer.subscribe(interested_topics)
    logging.info(f"Subscribed to topics: {interested_topics}")

    while True:
        try:
            message = consumer.poll(timeout=1.0)

            if message is None: continue

            if message.error():

                if message.error().code() == KafkaError._PARTITION_EOF:
                    logging.error(f"End of partition reached {message.topic()} {message.partition()} {message.offset()}")
                elif message.error():
                    logging.error(f"Consumer error: {msg.error()}")
                    raise KafkaException(message.error())
                elif "UNKNOWN_TOPIC_OR_PART" in str(message.error()):
                    logging.info(f"Topic not found: {message.topic()}... making topics: {interested_topics}")
                    consumer.create_topics(interested_topics)

            # Process message
            topic = message.topic(); key = message.key(); value = message.value()
            logging.info(f"Received message: {topic} {key} {value}")
            await pub_to_timescale(json.loads(value))

        except Exception as e:
            logging.error(f"Error in Kafka listener: {e}")
            exit(1)


@asynccontextmanager
async def start_kafka_listener(application: FastAPI):
    await kafka_listener()  # This will run kafka_listener as a background task
    yield
    logging.info("Stopping Kafka listener")

app = FastAPI(lifespan=start_kafka_listener)
# app.include_router(token_routes.router, prefix="/api", tags=["tokens"])

if __name__ == "__main__":
    try:
        logging.info("Starting API")
        config = uvicorn.Config(app, host=api_host, port=int(api_port), loop="asyncio")
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        logging.error(f"Error in main: {e}")
        exit(1)
