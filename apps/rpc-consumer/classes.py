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
        if isinstance(url, dict):
            self.url = url["rpc"]
            self.url_2 = url["http"]
        else:
            self.url = url
            self.url_2 = None

        self.commitment = commitment
        self.encoding = encoding
        self.async_client = AsyncClient(url)
        self.async_client_2 = AsyncClient(self.url_2) if self.url_2 else None
        self.subscription_id = None
        self.start_time = time.time()
        self.request_counter = 0

    async def connect_websocket(self):
        logging.info(f"Connecting to {self.url}")
        try:
            return await connect(self.url)
        except Exception as e:
            logging.error(f"Error connecting to websocket: {e}")
            time.sleep(1)
            return await self.connect_websocket()

    async def subscribe(self, websocket, subscription_type, pubkey=None, filter=None):
        self.request_counter += 1
        elapsed_time = time.time() - self.start_time

        if elapsed_time >= 1:
            logging.info(f"RPS: {self.request_counter}")
            self.request_counter = 0
            self.start_time = time.time()

        if filter is not None:
            await websocket.logs_subscribe(filter)
            logging.info("Subscribing to logs with filter")
        else:
            logging.info("Subscribing to logs without filter")
            await websocket.logs_subscribe()

        first_resp = await websocket.recv()
        self.subscription_id = first_resp[0].result
        logging.info(f"Subscribed with id {self.subscription_id}")
        return self.subscription_id

    async def unsubscribe(self, websocket):
        await websocket.logs_unsubscribe(self.subscription_id)

    async def _listen_loop(self, websocket, callback):
        try:
            while True:
                next_resp = await websocket.recv()
                if next_resp:
                    client = self.async_client_2 if self.async_client_2 else self.async_client
                    await callback(client,next_resp[0].to_json())
                    self._update_request_counter()
        except Exception as e:
            logging.error(f"Error in listen/callback : {e}")
            await self._reconnect_and_listen(callback)

    async def _reconnect_and_listen(self, callback):
        logging.info("Reconnecting...")
        time.sleep(1)
        await self.listen(callback)

    def _update_request_counter(self):
        self.request_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= 10:
            logging.info(f"RPS: {round(self.request_counter / elapsed_time)}")
            self.request_counter = 0
            self.start_time = time.time()


class LogsSubscriptionHandler(BaseSubscriptionHandler):
    def __init__(self, url, filter=None):
        super().__init__(url)
        self.filter = filter

    async def listen(self, callback):
        websocket = await self.connect_websocket()
        await self.subscribe(websocket, "logs", filter=self.filter)
        await self._listen_loop(websocket, callback)


class ProgramSubscriptionHandler(BaseSubscriptionHandler):
    def __init__(self, url, pubkey):
        super().__init__(url)
        self.pubkey = pubkey

    async def listen(self, callback):
        websocket = await self.connect_websocket()
        await self.subscribe(websocket, "program", pubkey=self.pubkey)
        await self._listen_loop(websocket, callback)

class Helpers:
    @staticmethod
    async def token_meta_from_transaction(client, transaction_signature: Signature):
        data = {}
        try:
            res = await client.get_transaction(transaction_signature, max_supported_transaction_version=1)
            res = json.loads(res.value.to_json())
            post_token_balances = res.get("meta", {}).get("postTokenBalances", [])
            for balance in post_token_balances:
                data["token_address"] = balance.get("mint")
                data["owner"] = balance.get("owner")
                data["initial_supply"] = balance.get("uiTokenAmount", {}).get("amount")
                data["decimals"] = balance.get("uiTokenAmount", {}).get("decimals")
                data["mint"] = balance.get("mint")
                logging.info(data)
            return data
        except Exception as e:
            logging.error(f"Error fetching token meta: {e}, retrying...")
            time.sleep(1)
            return await Helpers.token_meta_from_transaction(client, transaction_signature)
