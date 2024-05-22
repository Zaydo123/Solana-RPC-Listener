from classes import LogsSubscriptionHandler, Helpers, ProgramSubscriptionHandler
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solders.signature import Signature
from solders.pubkey import Pubkey
from colorama import Fore, init
from solana.rpc.async_api import AsyncClient
from dotenv import load_dotenv, find_dotenv
import json, time, os, urllib3, asyncio
from threading import Thread
from queue import Queue
from redis import Redis
import logging, base58

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
init(autoreset=True)
load_dotenv(find_dotenv(".env"))


TOKEN_PROGRAM_PUBLIC_KEY = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
RAYDIUM_PUBLIC_KEY = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
RAYDIUM_PUBLIC_KEY_STRING = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"

#r = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), password=os.getenv("REDIS_PASSWORD"), decode_responses=True) - for password protected redis
r = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)
open_channels = r.pubsub_channels()

for channel in open_channels:
    logging.info(f"Consumers in channel: {channel}")
    r.publish(channel, ":producerConnected")


async def callback_raydium(ctx: AsyncClient, data: dict):
    json_data = json.loads(data)
    for log in json_data["result"]["value"]["logs"]:
        if "initialize2" in log:

            if json_data["result"]["value"]["err"] != None: 
                return
            
            json_data["result"]["value"]["signature"]
            signature = Signature.from_string(json_data["result"]["value"]["signature"])
            try:
                transaction = await ctx.get_transaction(signature, max_supported_transaction_version=0, commitment="confirmed",encoding="jsonParsed")

            except Exception as e:
                logging.error(f"Error fetching transaction: {e}")
                return
            
            parsed_tx = json.loads(transaction.to_json())

            accounts = []
            for instruction in parsed_tx["result"]["transaction"]["message"]["instructions"]:
                if instruction["programId"] == RAYDIUM_PUBLIC_KEY_STRING:
                    accounts = instruction["accounts"]
                    logging.info(True)
                    break
                
            if len(accounts) == 0:
                logging.info("No accounts found")
                return
            else:
                token1Address = accounts[8]
                token2Address = accounts[9]
                logging.info(f"New Pool Created: {token1Address} - {token2Address}")

            r.publish("pairs", json.loads({"token1": token1Address, "token2": token2Address}))
            return
        
asyncio.run(ProgramSubscriptionHandler({"rpc":"wss://api.mainnet-beta.solana.com", "http":"https://api.mainnet-beta.solana.com"}, RAYDIUM_PUBLIC_KEY).listen(callback_raydium))
