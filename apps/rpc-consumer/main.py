from classes import Helpers, LogsSubscriptionHandler
from solders.signature import Signature
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from dotenv import load_dotenv, find_dotenv
import json, os, asyncio
from threading import Thread
import logging, colorama
from colorama import Fore, Back, init
from redis import Redis

init(autoreset=True)

logging.basicConfig(level=logging.INFO, format=f'{Fore.YELLOW}[Listener]{Fore.RESET} %(asctime)s - %(levelname)s - %(message)s')
load_dotenv(find_dotenv(".env"))

TOKEN_PROGRAM_PUBLIC_KEY = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
RAYDIUM_PUBLIC_KEY_STRING = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_PUBLIC_KEY = Pubkey.from_string(RAYDIUM_PUBLIC_KEY_STRING)

#r = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), password=os.getenv("REDIS_PASSWORD"), decode_responses=True) - for password protected redis
r = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)
open_channels = r.pubsub_channels()

for channel in open_channels:
    logging.info(f"Consumers in channel: {channel}")
    r.publish(channel, ":producerConnected")


last_sig = None

async def callback_raydium(ctx: AsyncClient, data: str):
    global last_sig
    json_data = json.loads(data)
    for log in json_data["result"]["value"]["logs"]:
        if "initialize2" in log:

            if json_data["result"]["value"]["err"] != None: 
                return
            
            sig_string = json_data["result"]["value"]["signature"]
            
            if sig_string == last_sig:
                logging.info("Duplicate signature")
                return

            last_sig = sig_string
            
            signature = Signature.from_string(json_data["result"]["value"]["signature"])
            try:
                transaction = await ctx.get_transaction(signature, max_supported_transaction_version=0, commitment="confirmed",encoding="jsonParsed")

            except Exception as e:
                logging.error(f"Error fetching transaction: {e}")
                return
            
            tx_str = transaction.to_json()
            parsed_tx = json.loads(tx_str)

            accounts = []

            for instruction in parsed_tx["result"]["transaction"]["message"]["instructions"]:
                if instruction["programId"] == RAYDIUM_PUBLIC_KEY_STRING:
                    accounts = instruction["accounts"]
                    break

            if len(accounts) == 0:
                logging.info("No accounts found")
                return
            else:
                base = accounts[8]
                quote = accounts[9]
                base_pool_account = accounts[10]
                quote_pool_account = accounts[11]
                logging.info(f"{Fore.GREEN}New pair found: {base} - {quote}{Fore.RESET}")


            data = {"baseToken": base, "quoteToken": quote, "sig": sig_string, "full_tx": tx_str}
            r.publish("pairs", json.dumps(data))
            return

asyncio.run(LogsSubscriptionHandler({"rpc":os.environ.get("WSS_PROVIDER"), "http":os.environ.get("HTTP_PROVIDER")}).listen(callback_raydium))

