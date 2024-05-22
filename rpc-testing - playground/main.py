import asyncio
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solana.rpc.websocket_api import connect
from solana.rpc.async_api import AsyncClient
from colorama import Fore, init
import urllib3
import json, time

# temp stuff for data collection
from queue import Queue
from threading import Thread
q = Queue()

def queue_to_file():
    with open("data.txt", "a+") as f:
        while not q.empty():
            sz = q.qsize()
            if sz>0:
                for _ in range(sz):
                    f.write(q.get() + "\n")
                print("Data written to file")

def continuous_write():
    while True:
        time.sleep(1)
        queue_to_file()

Thread(target=continuous_write).start()

init(autoreset=True)

class BaseSubscriptionHandler:
    def __init__(self, url, commitment="confirmed", encoding="jsonParsed"):
        
        if type(url) == dict:
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
        print(f"Connecting to {self.url}")
        try:
            return await connect(self.url)
        except Exception as e:
            print(f"{Fore.RED}[Error]: {e}")
            time.sleep(1)
            print("Retrying...")
            await self.connect_websocket()

    async def subscribe(self, websocket, subscription_type, pubkey=None, filter=None):
        self.request_counter += 1
        elapsed_time = time.time() - self.start_time

        if elapsed_time >= 1:
            print(f"RPS: {self.request_counter}")
            self.request_counter = 0
            self.start_time = time.time()

        if filter != None:
            await websocket.logs_subscribe(filter)
            print("-   Subscribing to logs with filter")
        else:
            print("-   Subscribing to logs without filter")
            await websocket.logs_subscribe()

        first_resp = await websocket.recv()
        self.subscription_id = first_resp[0].result
        print(f"-   Subscribed with id {self.subscription_id}")
        return self.subscription_id

    async def unsubscribe(self, websocket):
        await websocket.logs_unsubscribe(self.subscription_id)


class LogsSubscriptionHandler(BaseSubscriptionHandler):
    def __init__(self, url, filter=None):
        super().__init__(url)
        self.filter = filter

    async def listen(self, callback):
        websocket = await self.connect_websocket()
        await self.subscribe(websocket, "logs", filter=self.filter)
        try:
            while True:
                next_resp = await websocket.recv()
                if next_resp:
                    if self.async_client_2:
                        await callback(json.loads(next_resp[0].to_json()), self.async_client_2)
                    else:
                        await callback(json.loads(next_resp[0].to_json()), self.async_client)
                    self.request_counter += 1
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time >= 5:  # Change this to the number of seconds you want
                        print(f"RPS: {self.request_counter / elapsed_time}")
                        self.request_counter = 0
                        self.start_time = time.time()

        except Exception as e:
            print(e.with_traceback(None))
            print("Error in listen, reconnecting...")
            await self.connect_websocket()
            await self.listen(callback)


async def ec2(msg, client):
    if msg["result"]["value"]["err"]:
        return
    logs = msg["result"]["value"]["logs"]
    signature = msg["result"]["value"]["signature"]
    for _ in logs:
        if "Program log: Instruction: InitializeMint" in _:
            print(Fore.RED+"Mint event" + " " + signature)
            print(await token_meta_from_transaction(client, Signature.from_string(signature)))
            q.put(signature)


async def token_meta_from_transaction(client,transaction_signature: Signature):    
    data = {}
    try:
        res = await client.get_transaction(transaction_signature, max_supported_transaction_version=1)
        res = json.loads(res.value.to_json())
        post_token_balances = res.get("meta", {}).get("postTokenBalances", [])
        for i in range(len(post_token_balances)):
            data["token_address"] = post_token_balances[i].get("mint")
            data["owner"] = post_token_balances[i].get("owner")
            data["initial_supply"] = post_token_balances[i].get("uiTokenAmount").get("amount")
            data["decimals"] = post_token_balances[i].get("uiTokenAmount").get("decimals")
            data["mint"] = post_token_balances[i].get("mint")
            print(data)
        return data
    except Exception as e:
        print(f"{Fore.RED}[Error]: {e}\n retrying...")
        time.sleep(1)
        await token_meta_from_transaction(client,transaction_signature)

class ProgramSubscriptionHandler(BaseSubscriptionHandler):
    def __init__(self, url, pubkey):
        super().__init__(url)
        self.pubkey = pubkey

    async def listen(self, callback):
        websocket = await self.connect_websocket()
        await self.subscribe(websocket, "program", pubkey=self.pubkey)
        try:
            while True:
                next_resp = await websocket.recv()
                if next_resp:
                    await callback(json.loads(next_resp[0].to_json()))
                    self.request_counter += 1
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time >= 5:
                        print(f"RPS: {self.request_counter / elapsed_time}")
                        self.request_counter = 0
                        self.start_time = time.time()

        except Exception as e:
            print(e.with_traceback(None))
            print("Error in listen, reconnecting...")
            await self.connect_websocket()
            time.sleep(1)
            await self.listen(callback)


pk = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
#urls = {"rpc" : "ws://127.0.0.1:8900", "http" : "http://127.0.0.1:8899"}
urls = {"rpc" : "ws://api.mainnet-beta.solana.com", "http" : "https://api.mainnet-beta.solana.com"}


#urls = "wss://api.mainnet-beta.solana.com"
#asyncio.run(LogsSubscriptionHandler(urls, filter=RpcTransactionLogsFilterMentions(pk)).listen(ec2))

asyncio.run(ProgramSubscriptionHandler(urls, pk).listen(ec3))
