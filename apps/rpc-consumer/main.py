from classes import LogsSubscriptionHandler, TransactionSubscriptionHandler, Transaction
from solders.transaction_status import ParsedInstruction # temporary
from solders.rpc.config import RpcTransactionLogsFilterMentions
from collections.abc import Mapping, Iterable
from solana.rpc.async_api import AsyncClient
from dotenv import load_dotenv, find_dotenv
from solders.signature import Signature
from colorama import Fore, Back, init
from solders.pubkey import Pubkey
from helpers import HealthTask
from threading import Thread
import json, os, asyncio
import logging, colorama
from redis import Redis
import traceback
import time
import os

# Initialize colorama
init(autoreset=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format=f'{Fore.YELLOW}[Listener]{Fore.RESET} %(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(find_dotenv(".env"))

# Configuration
TOKEN_PROGRAM_PUBLIC_KEY = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
RAYDIUM_PUBLIC_KEY_STRING = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_PUBLIC_KEY = Pubkey.from_string(RAYDIUM_PUBLIC_KEY_STRING)
NEW_PAIRS_CHANNEL = os.getenv("REDIS_NEW_PAIRS_CHANNEL")
WRAPPED_SOL_PUBKEY_STRING = "So11111111111111111111111111111111111111112"
RAYDIUM_AMM_ADDRESS = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"

# Redis connection
redis_client = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)

# Redis health task
failure_count = 0
def handle_redis_failure():
    global failure_count
    logging.error("Redis health check failed")
    failure_count += 1
    if failure_count >= 5:
        # emergency exit if redis fails
        os._exit(1) 
        

health_task = HealthTask(redis_client, 10, handle_redis_failure)
Thread(target=health_task.run).start()

# Global variables
last_base = None
last_quote = None
subscriptions = {}

def initialize_redis():
    """Initialize Redis and publish a welcome message."""
    open_channels = redis_client.pubsub_channels()
    for channel in open_channels:
        logging.info(f"Consumers in channel: {channel}")
        redis_client.publish(channel, '{"message": "[>] Hello from the transaction listener"}')

async def swap_callback(ctx: AsyncClient, data: str, target_token: str):
    """Handle swap callback for transactions."""
    json_data = json.loads(data)

    if json_data["result"]["value"]["err"] is not None:
        return
    
    for log in json_data["result"]["value"]["logs"]:
        if log.startswith("Program log: err:"):
            return

    swap_data = None

    try:
        signature_str = json_data["result"]["value"]["signature"]
        signature = Signature.from_string(json_data["result"]["value"]["signature"])
        try:
            logging.info(signature_str)
            transaction = await ctx.get_transaction(signature, max_supported_transaction_version=0, commitment="confirmed", encoding="jsonParsed")
            swap_data = await Transaction.get_swap(transaction, target_token)
            redis_client.publish(f"swap-{target_token}", json.dumps(swap_data.to_json()))
            logging.info("----- SWAP ------\n" + json.dumps(swap_data.to_json(), indent=4) + "\n------------------")
            
        except Exception as e:
            logging.error("Error fetching transaction from RPC")
            logging.error(traceback.format_exc() + "\n-------")
            return
    

        target_channel = f"swap-{swap_data.token_addr}"
        logging.info(target_channel)
        redis_client.publish(target_channel, json.dumps(swap_data.to_json()))

    except Exception as e:
        logging.error("Error processing transaction", exc_info=True)
        return

async def callback_raydium(ctx: AsyncClient, data: str):
    global last_base, last_quote
    json_data = json.loads(data)
    
    for log in json_data["result"]["value"]["logs"]:
        
        if json_data["result"]["value"]["err"] is None:

            sig_string = json_data["result"]["value"]["signature"]
        
            if log.startswith("Program log: initialize2"):
                
                mint_log_info = log[48:]
                token_mint_timestamp = mint_log_info.split("open_time: ")[1].split(",")[0]
                delta = int(time.time()) - int(token_mint_timestamp) # may be negative if mint is scheduled in the future
                logging.info("Caught new pair within: " + str(delta) + " seconds of launch") 

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
                    pool_account = accounts[4]
                    base = accounts[8]
                    quote = accounts[9]

                # Swap base and quote if quote is WRAPPED_SOL_PUBKEY_STRING
                if base == WRAPPED_SOL_PUBKEY_STRING:
                    base, quote = quote, base

                if base == last_base and quote == last_quote:
                    logging.info(f"{Fore.RED}Pair already exists{Fore.RESET}")
                    return

                last_base = base
                last_quote = quote

                logging.info(f"{Fore.GREEN}New pair found: {base} - {quote}{Fore.RESET}")

                data = {"message":"new pair", "mintTimestamp": token_mint_timestamp, "baseToken": base, "quoteToken": quote, "sig": sig_string, "poolAccount": pool_account, "full_tx": tx_str}
                redis_client.publish(NEW_PAIRS_CHANNEL, json.dumps(data))

                subscription_key = f"swaps-{base}-{quote}"
                if subscription_key not in subscriptions:
                    pool_account_filter = RpcTransactionLogsFilterMentions(Pubkey.from_string(pool_account))
                    handler_swaps = TransactionSubscriptionHandler({"rpc":os.environ.get("WSS_PROVIDER_TRANSACTIONS"), "http":os.environ.get("HTTP_PROVIDER_TRANSACTIONS")}, filter=pool_account_filter)
                    subscriptions[subscription_key] = handler_swaps
                    asyncio.create_task(handler_swaps.listen(swap_callback, base)) # target_token is the base token in the pair (makes it easier to filter out noise in swap transactions)
                    asyncio.create_task(unsubscribe_after_timeout(subscription_key, duration=50)) 
                    logging.info(f"Subscribed to {subscription_key}")
                else:
                    logging.info(f"{Fore.RED}Subscription for {subscription_key} already exists{Fore.RESET}")
            else: # Burn instruction
                if "Burn" in log:
                    signature = Signature.from_string(json_data["result"]["value"]["signature"])
                    logging.info(f"Burn TX: {signature}")
                    try:
                        transaction = await ctx.get_transaction(signature, max_supported_transaction_version=0, commitment="confirmed",encoding="jsonParsed")
                        res = await ctx.get_transaction(Signature.from_string("E4jxokMPvmh5QM3yWBUunFrRdizCFY32swy8i3SWpf2U4NLx8Ea5BTbZJHF9fNbAsmsiFvJfTBQUyC2Qua99Hbq"), max_supported_transaction_version=0, commitment="confirmed", encoding="jsonParsed")
                        ct = 0
                        for instruction in res.value.transaction.meta.inner_instructions:
                            for i in instruction.instructions:
                                ct += 1
                                if type(i)==ParsedInstruction:
                                    if(i.parsed["type"].find("burn") != -1):
                                        logging.info(f"Burn in instruction : {ct}" )

                    except Exception as e:
                        logging.error(f"Error fetching transaction: {e}")
                        return
                    

async def unsubscribe_after_timeout(subscription_key: str, duration: int):
    """Unsubscribe after a specified timeout."""
    await asyncio.sleep(duration)
    if subscription_key in subscriptions:
        handler = subscriptions.pop(subscription_key)
        await handler.unsubscribe()
        logging.info(f"Unsubscribed from {subscription_key} after {duration} seconds")


async def main():
    """Main entry point for the async tasks."""
    filter_raydium = RpcTransactionLogsFilterMentions(RAYDIUM_PUBLIC_KEY)
    handler_mint = LogsSubscriptionHandler(
        {
            "rpc": os.getenv("WSS_MAINNET"),
            "http": os.getenv("HTTP_PROVIDER_MAIN")
        },
        filter=filter_raydium
    )
    subscriptions["raydium"] = handler_mint
    mint_task = handler_mint.listen(callback_raydium)
    await asyncio.gather(mint_task)

if __name__ == "__main__":
    initialize_redis()
    asyncio.run(main())
