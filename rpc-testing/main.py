import asyncio
from solders.pubkey import Pubkey
from asyncstdlib import enumerate
from solana.rpc.websocket_api import connect
from colorama import Fore, Back, init
import json
init(autoreset=True)

class Listener:
    def __init__(self, url, pubkey, commitment="confirmed", encoding="jsonParsed"):
        self.url = url
        self.pubkey = pubkey
        self.commitment = commitment
        self.encoding = encoding
        self.count = 0
        self.minted_coin_addresses = []

    async def connect_websocket(self):
        return await connect(self.url)

    async def subscribe(self, websocket):
        await websocket.program_subscribe(self.pubkey, commitment=self.commitment, encoding=self.encoding)
        first_resp = await websocket.recv()
        subscription_id = first_resp[0].result
        print("Subscribed with id", subscription_id)
        return subscription_id
    
    async def mint_processor(self, msg):
        if msg.result.value.account.data.parsed["type"] == "mint":
            if msg.result.value.account.data.parsed["info"].get("extensions"):
                for extension in msg.result.value.account.data.parsed["info"]["extensions"]:
                    if extension["extension"] == "tokenMetadata":
                        if int(msg.result.value.account.data.parsed["info"]["supply"]) > 1:
                            self.minted_coin_addresses.append(extension)
                            print(Fore.GREEN + "Mint found [COIN]: " + Fore.RED + extension["state"]["name"] + ": https://dexscreener.com/solana/" + str(extension["state"]["mint"]))
                        elif int(msg.result.value.account.data.parsed["info"]["supply"]) == 1:
                            #print(msg.result.value.account.data.parsed)
                            print(Fore.GREEN + "Mint found [NFT]: " + Fore.RED + extension["state"]["name"])
                            print(Fore.GREEN + "                : " + Fore.RED + extension["state"]["uri"])
                            print("-------------------")
                        else:
                            print(Fore.GREEN + "Mint found [UNKNOWN]: " + Fore.RED + extension["state"]["name"] + " Supply: " + str(msg.result.value.account.data.parsed["info"]["supply"]))
                            print(Fore.GREEN + "Mint found [UNKNOWN]: " + Fore.RED + extension["state"]["uri"])
                            print("-------------------")

    async def process_message(self, msg):
        msg = msg.to_json()
        print(msg)
        print("-------------------")
        #if json.loads(msg).result.value.account.data.parsed.type == "mint":
        #    await self.mint_processor(msg)
        #else:
        #    print(Fore.YELLOW + "Unknown message type: " + msg.value.account.data.parsed.type)

    async def listen(self):
        websocket = await self.connect_websocket()
        subscription_id = await self.subscribe(websocket)
        while True:
            next_resp = await websocket.recv()
            self.count += 1
            msg = next_resp[0]
            await self.process_message(msg)

            if self.count == 100000:
                break

        await websocket.account_unsubscribe(subscription_id)
        await websocket.close()
        print("Unsubscribed")

asyncio.run(Listener("")).listen())
