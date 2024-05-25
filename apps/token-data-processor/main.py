from solana.rpc.async_api import AsyncClient
from apps.helpers.redis_health import HealthTask
from dotenv import load_dotenv, find_dotenv
from solders.signature import Signature
from colorama import Fore, Back, init
from solders.pubkey import Pubkey
from threading import Thread
import json, os, asyncio
from time import sleep
from redis import Redis, ConnectionError
import logging, sys

init(autoreset=True)
logging.basicConfig(level=logging.INFO, format=f'{Fore.LIGHTRED_EX}[Processor]{Fore.RESET} %(asctime)s %(levelname)s - %(message)s')
load_dotenv(find_dotenv(".env"))
logging.info("Booting up...")

p = None
r = None


def listen_for_new_pairs():
    while True:
        try:
            p.subscribe("pairs")
            for message in p.listen():
                if message["type"] != "message" or message["channel"] != "pairs":
                    continue
                print(message["data"])
        except (ConnectionError, Exception) as e:
            logging.error(f"Error listening for new pairs: {e}")
            sleep(5)

def connect_redis(from_health=False):
    global r, p
    while True:
        try:
            r = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)
            p = r.pubsub()
            r.ping()  # will throw if no conn
            if not from_health:
                Thread(target=health_thread_target).start()
            Thread(target=listen_for_new_pairs).start()  # Start the listener thread
            logging.info(f"Connected to Redis at {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}")
            break
        except (ConnectionError, Exception) as e:
            logging.critical(f"Error connecting to Redis: {e}")
            if not from_health:
                logging.critical("Exiting...")
                sys.exit(1)
            sleep(5)

def health_thread_target():
    global r
    def handle_redis_failure():
        global r
        try:
            connect_redis(True)
        except Exception as e:
            logging.critical(f"{Back.LIGHTRED_EX}Failed to reconnect to Redis:{Back.RESET} {e}")

    try:
        health_task = HealthTask(r, 5, handle_redis_failure).run()
    except Exception as e:
        logging.critical(f"Health thread exception: {e}")

connect_redis()

while True:
    sleep(1)
