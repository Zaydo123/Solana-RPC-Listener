from solders.rpc.config import RpcTransactionLogsFilterMentions
from classes import LogsSubscriptionHandler
from solders.signature import Signature
from solders.pubkey import Pubkey
from decimal import Decimal, getcontext
from collections.abc import Mapping, Iterable
from solana.rpc.async_api import AsyncClient
from dotenv import load_dotenv, find_dotenv
import json, os, asyncio
from threading import Thread
import logging, colorama
from colorama import Fore, Back, init
from redis import Redis
import time
import traceback

init(autoreset=True)
logging.basicConfig(level=logging.INFO, format=f'{Fore.YELLOW}[Listener]{Fore.RESET} %(asctime)s - %(levelname)s - %(message)s')
load_dotenv(find_dotenv(".env"))
getcontext().prec = 18

TOKEN_PROGRAM_PUBLIC_KEY = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
RAYDIUM_PUBLIC_KEY_STRING = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_PUBLIC_KEY = Pubkey.from_string(RAYDIUM_PUBLIC_KEY_STRING)
NEW_PAIRS_CHANNEL = os.getenv("REDIS_NEW_PAIRS_CHANNEL")
WRAPPED_SOL_PUBKEY_STRING = "So11111111111111111111111111111111111111112"
RAYDIUM_AMM_ADDRESS = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"

#r = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), password=os.getenv("REDIS_PASSWORD"), decode_responses=True) - for password protected redis
r = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)
open_channels = r.pubsub_channels()

for channel in open_channels:
    logging.info(f"Consumers in channel: {channel}")
    r.publish(channel, '{"message": "[>] Hello from the transaction listener"}')

last_base = None
last_quote = None

subscriptions = {}

#CaShxDq2Vbdp2XryjDdUZthbTzwYsvKuH6Knn9pPi4xU - burn address
# has a lot of problems fetching transactions with many transfers - e.g. with bonk bot

class DecimalEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, Mapping):
            return '{' + ', '.join(f'{self.encode(k)}: {self.encode(v)}' for (k, v) in obj.items()) + '}'
        if isinstance(obj, Iterable) and (not isinstance(obj, str)):
            return '[' + ', '.join(map(self.encode, obj)) + ']'
        if isinstance(obj, Decimal):
            return f'{obj.normalize():f}'  # using normalize() gets rid of trailing 0s, using ':f' prevents scientific notation
        return super().encode(obj)

def detect_key_transaction(pre_balances, post_balances, amm_address):
    balance_changes = {}

    # initialize bals
    for entry in pre_balances:
        pubkey = entry['accountIndex']
        balance_changes[pubkey] = {
            'pre_balance': Decimal(entry['uiTokenAmount']['uiAmountString']),
            'post_balance': None,  # To be updated
            'owner': entry['owner'],
            'mint': entry['mint']
        }

    # update post bals
    for entry in post_balances:
        pubkey = entry['accountIndex']
        if pubkey in balance_changes:
            balance_changes[pubkey]['post_balance'] = Decimal(entry['uiTokenAmount']['uiAmountString'])
        else:
            balance_changes[pubkey] = {
                'pre_balance': Decimal('0'),
                'post_balance': Decimal(entry['uiTokenAmount']['uiAmountString']),
                'owner': entry['owner'],
                'mint': entry['mint']
            }

    # process txs
    sells = []
    buys = []
    for changes in balance_changes.values():
        if changes['post_balance'] is None:
            changes['post_balance'] = 0  # Assume zero if no post balance
        change = changes['post_balance'] - changes['pre_balance']
        if change != 0 and changes['owner'] != amm_address:
            transaction_type = "buy" if change > 0 else "sell"
            transaction = {
                "account_owner": changes['owner'],
                "transaction_type": transaction_type,
                "token_amount": abs(change),
                "token_mint": changes['mint']
            }
            if transaction_type == "sell":
                sells.append(transaction)
            else:
                buys.append(transaction)

    # find main tx
    key_transaction = None
    for sell in sells:
        for buy in buys:
            if sell['account_owner'] == buy['account_owner']:
                key_transaction = {
                    "account_owner": sell['account_owner'],
                    "sell_amount": sell['token_amount'],
                    "sell_mint": sell['token_mint'],
                    "buy_amount": buy['token_amount'],
                    "buy_mint": buy['token_mint']
                }
                return key_transaction  # !! Assuming one key swap per call, return early

    return key_transaction



async def swap_callback(ctx: AsyncClient, data: str):
    json_data = json.loads(data)

    if json_data["result"]["value"]["err"] != None:
        print(Fore.RED + json_data["result"]["value"]["signature"] + " - Transaction failed" + Fore.RESET)
        return
    
    for log in json_data["result"]["value"]["logs"]:
        if log[0:17] == "Program log: err:":
            print(Fore.RED + json_data["result"]["value"]["signature"] + " - Transaction failed" + Fore.RESET)
            return
    
    try:
        signature = Signature.from_string(json_data["result"]["value"]["signature"])
        transaction = await ctx.get_transaction(signature, max_supported_transaction_version=0, commitment="confirmed",encoding="jsonParsed")

        transaction_data = json.loads(transaction.to_json())

        pre_token_balances = transaction_data['result']['meta']['preTokenBalances']
        post_token_balances = transaction_data['result']['meta']['postTokenBalances']
        key_transaction = detect_key_transaction(pre_token_balances, post_token_balances, RAYDIUM_AMM_ADDRESS)
        print(key_transaction)
        r.publish("swaps-" + key_transaction["buy_mint"] + "-" + key_transaction["sell_mint"], json.dumps(key_transaction,cls=DecimalEncoder))
        if key_transaction == None:
            print(Fore.RED + json_data["result"]["value"]["signature"] + " - No key transaction found" + Fore.RESET)

    except Exception as e:
        logging.error(f"Error fetching transaction", traceback.format_exc())
        return
    

async def callback_raydium(ctx: AsyncClient, data: str):
    global last_base, last_quote, swap_callback
    json_data = json.loads(data)
    
    for log in json_data["result"]["value"]["logs"]:
        
        if json_data["result"]["value"]["err"] == None:

            sig_string = json_data["result"]["value"]["signature"]
        
            if log[0:24] == "Program log: initialize2":
                
                mint_log_info = log[48:len(log)]
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

                if base == last_base and quote == last_quote:
                    logging.info(f"{Fore.RED}Pair already exists{Fore.RESET}")
                    return
                elif base == WRAPPED_SOL_PUBKEY_STRING:
                    logging.info(f"{Fore.RED}Wrapped Sol Base - Skipping...{Fore.RESET}")
                    return

                last_base = base
                last_quote = quote

                logging.info(f"{Fore.GREEN}New pair found: {base} - {quote}{Fore.RESET}")

                data = {"message":"new pair", "mintTimestamp": token_mint_timestamp, "baseToken": base, "quoteToken": quote, "sig": sig_string, "poolAccount": pool_account, "full_tx": tx_str}
                r.publish(NEW_PAIRS_CHANNEL, json.dumps(data))

                pool_account_filter = RpcTransactionLogsFilterMentions(Pubkey.from_string(pool_account))
                handler_swaps = LogsSubscriptionHandler({"rpc":os.environ.get("WSS_PROVIDER"), "http":os.environ.get("HTTP_PROVIDER")}, filter=pool_account_filter)
                subscription_swaps = asyncio.create_task(handler_swaps.listen(swap_callback))
                subscriptions["swaps-" + base + "-" + quote] = subscription_swaps

async def main():
    # Filter for Raydium public key
    filter_raydium = RpcTransactionLogsFilterMentions(RAYDIUM_PUBLIC_KEY)
    # Handler for new mints
    handler_mint = LogsSubscriptionHandler({"rpc": os.getenv("WSS_PROVIDER"), "http": os.getenv("HTTP_PROVIDER")}, filter=filter_raydium)
    mint_task = handler_mint.listen(callback_raydium)
    await asyncio.gather(mint_task)

if __name__ == "__main__":
    asyncio.run(main())
