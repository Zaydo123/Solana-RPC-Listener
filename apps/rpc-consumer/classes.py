from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solders.signature import Signature
from colorama import Fore, init
import json, time, logging, traceback, asyncio
from decimal import Decimal
from collections.abc import Mapping, Iterable


# Constants

LAMPORTS_PER_SOL = 1_000_000_000
SOLANA_PUB_ADDRESS = "So11111111111111111111111111111111111111112"
# ------------------------------

init(autoreset=True)


# ------- RPC Subscription Handlers -------

# Configure logging
logging.basicConfig(level=logging.INFO, format=f'{Fore.YELLOW}[Listener]{Fore.RESET} %(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logging.getLogger("urllib").setLevel(logging.WARNING)

class BaseSubscriptionHandler:
    def __init__(self, url, commitment="confirmed", encoding="jsonParsed"):
        self.url = url["rpc"] if isinstance(url, dict) else url
        self.url_2 = url.get("http") if isinstance(url, dict) else None
        self.commitment = commitment
        self.encoding = encoding
        self.async_client = AsyncClient(self.url)
        self.async_client_2 = AsyncClient(self.url_2) if self.url_2 else None
        self.subscription_id = None
        self.start_time = time.time()
        self.request_counter = 0
        self.websocket = None
        self.running = True

    async def connect_websocket(self):
        logging.info(f"Connecting to {self.url}")
        while True:
            try:
                return await connect(self.url)
            except Exception as e:
                logging.error(f"Error connecting to websocket: {e}")
                time.sleep(1)

    async def subscribe(self, websocket, filter=None):
        self.request_counter += 1
        elapsed_time = time.time() - self.start_time

        if elapsed_time >= 1:
            logging.info(f"RPS: {self.request_counter}")
            self.request_counter = 0
            self.start_time = time.time()

        if filter:
            await websocket.logs_subscribe(filter)
            logging.info("Subscribing to logs with filter")
        else:
            await websocket.logs_subscribe()
            logging.info("Subscribing to logs without filter")

        first_resp = await websocket.recv()
        self.subscription_id = first_resp[0].result
        logging.info(f"Subscribed with id {self.subscription_id}")
        return self.subscription_id

    async def unsubscribe(self):
        if self.websocket:
            await self.websocket.logs_unsubscribe(self.subscription_id)
            self.running = False
            await self.websocket.close()
            logging.info(f"Unsubscribed from {self.subscription_id}")

    async def _listen_loop(self, websocket, callback):
        self.websocket = websocket  # Store websocket reference
        client = self.async_client_2 or self.async_client
        try:
            while self.running:
                next_resp = await websocket.recv()
                if next_resp:
                    await callback(client, next_resp[0].to_json())
                    self._update_request_counter()
        except asyncio.CancelledError:
            logging.info("Listen loop was cancelled")
        except Exception as e:
            if self.running:  # Only log error if not intentionally stopped
                logging.error(f"Error in listen/callback: {traceback.format_exc()}")
                await self._reconnect_and_listen(callback)

    async def _reconnect_and_listen(self, callback):
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries and self.running:
            logging.info("Reconnecting...")
            await asyncio.sleep(3)  # Incremental back-off can be implemented here
            try:
                await self.listen(callback)
                break
            except Exception as e:
                logging.error(f"Attempt {retry_count + 1} failed: {traceback.format_exc()}")
                retry_count += 1
        if retry_count == max_retries:
            logging.error("Max retries reached, stopping reconnection attempts.")

    def _update_request_counter(self):
        self.request_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= 5:
            logging.info(f"RPS: {round(self.request_counter / elapsed_time)}")
            self.request_counter = 0
            self.start_time = time.time()

class LogsSubscriptionHandler(BaseSubscriptionHandler):
    def __init__(self, url, filter=None):
        super().__init__(url)
        self.filter = filter

    async def listen(self, callback):
        while self.running:
            websocket = await self.connect_websocket()
            try:
                await self.subscribe(websocket, filter=self.filter)
                await self._listen_loop(websocket, callback)
            except Exception as e:
                logging.error(f"Error in listen loop: {traceback.format_exc()}")
                await self._reconnect_and_listen(callback)



# ------- Transaction Detection -------

class Transaction:
    def __init__(self, token_addr, transaction_type, maker, amount_sol, fee_sol, block_time):
        self.token_addr = token_addr
        self.transaction_type = transaction_type
        self.maker = maker
        self.amount_sol = amount_sol
        self.fee_sol = fee_sol
        self.block_time = block_time


    def __repr__(self):
        return f"Transaction(token_addr={self.token_addr}, transaction_type={self.transaction_type}, maker={self.maker}, amount_sol={self.amount_sol}, fee_sol={self.fee_sol}, block_time={self.block_time})"

    def __str__(self):
        return f"Transaction(token_addr={self.token_addr}, transaction_type={self.transaction_type}, maker={self.maker}, amount_sol={self.amount_sol}, fee_sol={self.fee_sol}, block_time={self.block_time})"

    def to_json(self):
        return {
            "token_addr": str(self.token_addr), # solders.signature.Signature
            "transaction_type": self.transaction_type, # str
            "maker": str(self.maker), # solders.pubkey.Pubkey
            "amount_sol": self.amount_sol, # float
            "fee_sol": self.fee_sol, # float
            "block_time": self.block_time # int
        }
    
    @staticmethod
    async def get_swap(trans_data, authority_address="5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"):
        post_balances = trans_data.value.transaction.meta.post_token_balances
        pre_balances = trans_data.value.transaction.meta.pre_token_balances
        fee_paid = trans_data.value.transaction.meta.fee / LAMPORTS_PER_SOL
        block_time = trans_data.value.block_time

        # Find the swap amount, maker address, and token address
        found_swap_amt = False
        found_maker = False
        maker = None
        token_addr = None
        
        for post_balance in post_balances:
                for pre_balance in pre_balances:
                    # Find the swap amount
                    if str(post_balance.owner) == authority_address and str(post_balance.mint) == SOLANA_PUB_ADDRESS and str(pre_balance.owner) == authority_address and str(pre_balance.mint) == SOLANA_PUB_ADDRESS:
                            pre_amount = float(pre_balance.ui_token_amount.ui_amount_string)
                            post_amount = float(post_balance.ui_token_amount.ui_amount_string)
                            swap_amt = post_amount - pre_amount
                            found_swap_amt = True
                    # Find the owner of the token
                    if str(post_balance.owner) != authority_address and pre_balance.owner == post_balance.owner and pre_balance.mint == post_balance.mint:
                        pre_amount = float(pre_balance.ui_token_amount.ui_amount_string)
                        post_amount = float(post_balance.ui_token_amount.ui_amount_string)
                        if pre_amount != post_amount:
                            maker = post_balance.owner
                            token_addr = post_balance.mint
                            found_maker = True

                    if found_swap_amt and found_maker:
                        break


        # Determine transaction type
        if swap_amt > 0:
            transaction_type = "Buy"
        elif swap_amt < 0:
            transaction_type = "Sell"
        else:
            transaction_type = "Unknown"



        return Transaction(token_addr, transaction_type, maker, abs(swap_amt), fee_paid, block_time)
    
