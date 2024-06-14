from solders.rpc.config import RpcTransactionLogsFilterMentions
from classes import LogsSubscriptionHandler, Transaction, DecimalEncoder
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


def detect_transactions(pre_balances, post_balances, amm_address):
    balance_changes = {}

    # Initialize and update balances
    for entry in pre_balances:
        pubkey = entry['accountIndex']
        balance_changes[pubkey] = {
            'pre_balance': Decimal(entry['uiTokenAmount']['uiAmountString']),
            'post_balance': Decimal('0'),  # Initialize to zero, update later
            'owner': entry['owner'],
            'mint': entry['mint']
        }

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

    # Collect transactions and convert Decimal to float for JSON serialization
    transactions = []
    for changes in balance_changes.values():
        change = changes['post_balance'] - changes['pre_balance']
        if change != 0:
            transactions.append({
                "account_owner": changes['owner'],
                "transaction_type": "buy" if change > 0 else "sell",
                "amount": float(abs(change)),  # Convert Decimal to float
                "token": changes['mint'],
                "is_amm": changes['owner'] == amm_address
            })

    # Return JSON string representation
    return transactions



async def swap_callback(ctx: AsyncClient, data: str):
    json_data = json.loads(data)

    if json_data["result"]["value"]["err"] != None:
        return
    
    for log in json_data["result"]["value"]["logs"]:
        if log[0:17] == "Program log: err:":
            return

    try:

        signature = Signature.from_string(json_data["result"]["value"]["signature"])
        try:
            transaction = await ctx.get_transaction(signature, max_supported_transaction_version=0, commitment="confirmed",encoding="jsonParsed")
        except Exception as e:
            logging.error(f"Error fetching transaction from RPC")
            logging.error(traceback.format_exc() + "\n-------")
            return
        transaction_data = json.loads(transaction.to_json())

        pre_token_balances = transaction_data['result']['meta']['preTokenBalances']
        post_token_balances = transaction_data['result']['meta']['postTokenBalances']
        block_time = transaction_data['result']['blockTime']

        transactions = detect_transactions(pre_token_balances, post_token_balances, RAYDIUM_AMM_ADDRESS)

        # Create a mapping of owner to their transactions for easy lookup
        transaction_vectors = []
        owner_transactions = {}


        for tx in transactions:
            owner = tx["account_owner"]
            new_tx_type = "buy" if tx["transaction_type"] == "sell" else "sell"
            transaction = Transaction(owner,new_tx_type, tx["token"], tx["amount"])
            transaction_vectors.append(transaction)
            if owner not in owner_transactions:
                owner_transactions[owner] = []
            owner_transactions[owner].append(transaction)

        final_transactions = []


        # Identify corresponding buy and sell transactions
        for amm_tx in transaction_vectors:
            if amm_tx.account_owner == RAYDIUM_AMM_ADDRESS:
                for other_tx in transaction_vectors:
                    if amm_tx.transaction_type == "sell" and other_tx.transaction_type == "buy" and amm_tx.token != other_tx.token:
                        amm_tx.other_account = other_tx.account_owner
                        other_tx.other_account = amm_tx.account_owner
                        print(f"Match found: {amm_tx} <-> {other_tx}")
                        final_transactions.append(amm_tx)
                        final_transactions.append(other_tx)
                        break
        
        if len(final_transactions) == 0:
            logging.error("No matching transactions found\nSignature: " + str(signature))
            return
        
        target_channel = "swap-"+ final_transactions[0].token + "-" + final_transactions[1].token
        key_transaction = {
            "block_time": block_time,
            "action": "swap",
            "transactions": [tx.to_json() for tx in final_transactions]
        }

        r.publish(target_channel, json.dumps(key_transaction,cls=DecimalEncoder))

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
                    logging.info(f"{Fore.RED}Wrapped Sol Base - {quote} - Skipping...{Fore.RESET}")
                    return

                last_base = base
                last_quote = quote

                logging.info(f"{Fore.GREEN}New pair found: {base} - {quote}{Fore.RESET}")

                data = {"message":"new pair", "mintTimestamp": token_mint_timestamp, "baseToken": base, "quoteToken": quote, "sig": sig_string, "poolAccount": pool_account, "full_tx": tx_str}
                r.publish(NEW_PAIRS_CHANNEL, json.dumps(data))

                pool_account_filter = RpcTransactionLogsFilterMentions(Pubkey.from_string(pool_account))
                handler_swaps = LogsSubscriptionHandler({"rpc":os.environ.get("WSS_PROVIDER_TRANSACTIONS"), "http":os.environ.get("HTTP_PROVIDER_TRANSACTIONS")}, filter=pool_account_filter)
                subscriptions["swaps-" + base + "-" + quote] = handler_swaps
                asyncio.create_task(handler_swaps.listen(swap_callback))
                print(Back.CYAN+"-----------------")
                print(subscriptions)
                print(Back.CYAN+"-----------------")

async def main():   
    # Filter for Raydium public key
    filter_raydium = RpcTransactionLogsFilterMentions(RAYDIUM_PUBLIC_KEY)
    # Handler for new mints
    handler_mint = LogsSubscriptionHandler({"rpc": os.getenv("WSS_MAINNET"), "http": os.getenv("HTTP_PROVIDER_MAIN")}, filter=filter_raydium)
    subscriptions["raydium"] = handler_mint
    mint_task = handler_mint.listen(callback_raydium)
    await asyncio.gather(mint_task)

if __name__ == "__main__":
    asyncio.run(main())
