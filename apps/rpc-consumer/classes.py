from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solders.signature import Signature
from colorama import Fore, init
import json, time, logging, traceback, asyncio
from decimal import Decimal
from collections.abc import Mapping, Iterable

init(autoreset=True)

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

    async def unsubscribe(self, websocket):
        await websocket.logs_unsubscribe(self.subscription_id)

    async def _listen_loop(self, websocket, callback):
        client = self.async_client_2 or self.async_client
        try:
            while True:
                next_resp = await websocket.recv()
                if next_resp:
                    await callback(client, next_resp[0].to_json())
                    self._update_request_counter()
        except Exception as e:
            logging.error(f"Error in listen/callback: {traceback.format_exc()}")
            await self._reconnect_and_listen(callback)

    async def _reconnect_and_listen(self, callback):
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
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
        while True:
            websocket = await self.connect_websocket()
            try:
                await self.subscribe(websocket, filter=self.filter)
                await self._listen_loop(websocket, callback)
            except Exception as e:
                logging.error(f"Error in listen loop: {traceback.format_exc()}")
                await self._reconnect_and_listen(callback)


class Transaction:
    def __init__(self, account_owner, transaction_type, token, amount):
        self.account_owner = account_owner
        self.other_account = None
        self.transaction_type = transaction_type
        self.token = token
        self.amount = amount

    def __str__(self):
        return f"{self.account_owner} {self.transaction_type} {self.amount} {self.token}"
    
    def __repr__(self):
        return self.__str__()
    
    def to_dict(self):
        return {
            "account_owner": self.account_owner,
            "other_account": self.other_account,
            "transaction_type": self.transaction_type,
            "token": self.token,
            "amount": self.amount
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())
    

class DecimalEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, Mapping):
            return '{' + ', '.join(f'{self.encode(k)}: {self.encode(v)}' for (k, v) in obj.items()) + '}'
        if isinstance(obj, Iterable) and (not isinstance(obj, str)):
            return '[' + ', '.join(map(self.encode, obj)) + ']'
        if isinstance(obj, Decimal):
            return f'{obj.normalize():f}'  # using normalize() gets rid of trailing 0s, using ':f' prevents scientific notation
        return super().encode(obj)