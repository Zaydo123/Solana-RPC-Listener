from solana.rpc.async_api import AsyncClient
from helpers import HealthTask
from dotenv import load_dotenv, find_dotenv
from solders.signature import Signature
from colorama import Fore, Back, init
from solders.pubkey import Pubkey
from threading import Thread
import json, os, asyncio
from time import sleep, time
from redis import Redis, ConnectionError
import logging, sys
import traceback

init(autoreset=True)
logging.basicConfig(level=logging.INFO, format=f'{Fore.LIGHTRED_EX}[Processor]{Fore.RESET} %(asctime)s %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logging.getLogger("solana").setLevel(logging.WARNING)

load_dotenv(find_dotenv(".env"))
logging.info("Booting up...")

client = AsyncClient(os.getenv("WSS_PROVIDER_MAIN"))
WRAPPED_SOL_PUBKEY_STRING = "So11111111111111111111111111111111111111112"
RAYDIUM_PUBLIC_KEY_STRING = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
PARSED_PAIRS_CHANNEL = os.getenv("REDIS_PARSED_PAIRS_CHANNEL")
PRICES_CHANNEL = os.getenv("REDIS_PRICES_CHANNEL")
NEW_PAIRS_CHANNEL = os.getenv("REDIS_NEW_PAIRS_CHANNEL")

p = None
r = None

class Token:
    
    def __init__(self, pubkey=None, symbol=None):
        self.pubkey = pubkey
        self.symbol = symbol
        self.owner_address = None
        self.freeze_authority = None
        self.mint_authority = None
        self.supply = None
        self.real_supply = None
        self.decimals = None
        self.is_initialized = None
        self.top_ownership_percent = None
        self.top_owners = {}

    async def get_info(self, commitment="confirmed"): # symbol is yet to be implemented
        rpc_data = await client.get_account_info_json_parsed(Pubkey.from_string(self.pubkey), commitment=commitment)
        rpc_data = json.loads(rpc_data.to_json())
        self.owner_address = rpc_data["result"]["value"]["owner"]
        self.freeze_authority = rpc_data["result"]["value"]["data"]["parsed"]["info"]["freezeAuthority"]
        self.mint_authority = rpc_data["result"]["value"]["data"]["parsed"]["info"]["mintAuthority"]
        self.supply_str = rpc_data["result"]["value"]["data"]["parsed"]["info"]["supply"]
        self.supply = int(self.supply_str)
        self.decimals = int(rpc_data["result"]["value"]["data"]["parsed"]["info"]["decimals"])
        self.real_supply = int(self.supply_str[0:len(self.supply_str)-self.decimals]) if self.supply > 0 else 0
        self.is_initialized = rpc_data["result"]["value"]["data"]["parsed"]["info"]["isInitialized"]

        logging.info(rpc_data["result"]["value"])

        largest_accounts_req = await client.get_token_largest_accounts(Pubkey.from_string(self.pubkey), commitment=commitment)
        largest_accounts = json.loads(largest_accounts_req.to_json())
        largest_accounts = largest_accounts["result"]["value"]
        percent_owned_by_largest_accounts = 0
        num_largest_accounts = 0

        for account in largest_accounts:
            percent_owned_by_account = float(account["uiAmountString"]) / self.real_supply
            num_largest_accounts += 1
            percent_owned_by_largest_accounts += percent_owned_by_account
            self.top_owners[account["address"]] = percent_owned_by_account

        self.top_ownership_percent = percent_owned_by_largest_accounts
        return self

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __str__(self):
        return f"Token: {self.symbol} - Supply: {self.supply} - Decimals: {self.decimals} - Real Supply: {self.real_supply} - Is Initialized: {self.is_initialized} - Top Ownership Percent: {self.top_ownership_percent} - Top Owners: {self.top_owners}"
    
    def __repr__(self):
        return self.__str__()
    

class Pair:
    def __init__(self, base_token=None, quote_token=None, base_pool_account=None, quote_pool_account=None, accounts=None):
        self.base_token = base_token if base_token else accounts[8]
        self.quote_token = quote_token if quote_token else accounts[9]
        self.base_pool_account = base_pool_account if base_pool_account else accounts[10]
        self.quote_pool_account = quote_pool_account if quote_pool_account else accounts[11]
        self.base_token_symbol = None
        self.quote_token_symbol = None
        self.base_pool_account_symbol = None
        self.quote_pool_account_symbol = None

    @staticmethod
    async def get_token_account_balance(token_account, commitment="finalized"):
        data = await client.get_token_account_balance(Pubkey.from_string(token_account), commitment=commitment)
        data = json.loads(data.to_json())
        return data["result"]["value"]["uiAmountString"] 

    @staticmethod
    async def get_token_price(base_pool_account, quote_pool_account, commitment="finalized"):
        bal_base_pool = await Pair.get_token_account_balance(base_pool_account, commitment)
        bal_quote_pool = await Pair.get_token_account_balance(quote_pool_account, commitment)
        return {"price":float(bal_quote_pool) / float(bal_base_pool), "base_pooled_balance": bal_base_pool, "quote_pooled_balance": bal_quote_pool}
    
    async def get_quote_token_price(self, commitment="finalized"):
        return await self.get_token_price(self.base_pool_account, self.quote_pool_account, commitment)
    
    async def get_base_token_price(self, commitment="finalized"):
        return await self.get_token_price(self.quote_pool_account, self.base_pool_account, commitment)

#----------------- Token Price Task  -----------------#
# follows the price of a pair and sets the price of the pubkey in the redis db and in pubsub until timelimit is reached

async def token_price_task(base_token,quote_token,base_address,quote_address, interval=5, timelimit=60):
    start_time = time()
    while time() - start_time < timelimit:
        try:
            pair_info = await Pair.get_token_price(base_address, quote_address)
            base_price = pair_info["price"]
            base_pool_balance = pair_info["base_pooled_balance"]
            quote_pool_balance = pair_info["quote_pooled_balance"]
            r.set(f"{base_address}-{quote_address}", base_price)
            r.publish(PRICES_CHANNEL, json.dumps({"timestamp": int(time()), "base": base_token, "quote": quote_token, "base_pooled_balance": base_pool_balance, "quote_pooled_balance": quote_pool_balance,  "base_price": base_price }))
            logging.info(f"{Fore.GREEN}{base_price}{Fore.RESET}")
            sleep(interval)
        except Exception as e:
            logging.error(f"Error in token price task: {e}")
            sleep(5)


async def new_pair_task(json_data):
    try:
        token = await Token(json_data["baseToken"]).get_info()
        r.set(f"{json_data['baseToken']}-info", token.to_json())
        r.publish(PARSED_PAIRS_CHANNEL, token.to_json())
        logging.info(f"Token info: {token}")
        try:

            accounts = json.loads(json_data["full_tx"])
            print(json_data)

            for instruction in accounts["result"]["transaction"]["message"]["instructions"]:
                if instruction["programId"] == RAYDIUM_PUBLIC_KEY_STRING:
                    accounts = instruction["accounts"]

            await asyncio.create_task(token_price_task(json_data["baseToken"],json_data["quoteToken"],accounts[10],accounts[11]))
        except Exception as e:
            logging.error(f"Error creating token price task: {traceback.format_exc()}")
        
    except Exception as e:
        logging.error(f"Error in new pair task: {traceback.format_exc()}")


async def listen_for_new_pairs():
    while True:
        try:
            p.subscribe(NEW_PAIRS_CHANNEL)
            for message in p.listen():
                if message["type"] != "message":
                    continue
                json_data = json.loads(message["data"])
                if json_data["message"].startswith("[>]"):
                    continue # ignore messages from the processor
                
                #if json_data["baseToken"] != WRAPPED_SOL_PUBKEY_STRING:
                else:
                    await new_pair_task(json_data)
                    

        except (ConnectionError, Exception) as e:
            #use traceback to get more info on the error
            logging.error(f"Error listening for new pairs: {e}")
            logging.error(traceback.format_exc())
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
            logging.info(f"Connected to Redis at {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}")
            asyncio.run(listen_for_new_pairs())
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

