from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solders.signature import Signature
from colorama import Fore, init
import json
import time
import logging

init(autoreset=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format=f'{Fore.YELLOW}[Listener]{Fore.RESET} %(asctime)s - %(levelname)s - %(message)s')

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
            logging.error(f"Error in listen/callback: {e}")
            await self._reconnect_and_listen(callback)

    async def _reconnect_and_listen(self, callback):
        logging.info("Reconnecting...")
        time.sleep(3)
        await self.listen(callback)

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
        websocket = await self.connect_websocket()
        await self.subscribe(websocket, filter=self.filter)
        await self._listen_loop(websocket, callback)

class Helpers:
    @staticmethod
    async def token_meta_from_transaction(client, transaction_signature: Signature):
        try:
            res = await client.get_transaction(transaction_signature, max_supported_transaction_version=1)
            res = json.loads(res.value.to_json())
            post_token_balances = res.get("meta", {}).get("postTokenBalances", [])
            data = [{
                "token_address": balance.get("mint"),
                "owner": balance.get("owner"),
                "initial_supply": balance.get("uiTokenAmount", {}).get("amount"),
                "decimals": balance.get("uiTokenAmount", {}).get("decimals"),
                "mint": balance.get("mint")
            } for balance in post_token_balances]
            return data
        except Exception as e:
            logging.error(f"Error fetching token meta: {e}, retrying...")
            time.sleep(1)
            return await Helpers.token_meta_from_transaction(client, transaction_signature)
