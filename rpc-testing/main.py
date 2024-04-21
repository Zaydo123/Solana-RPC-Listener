import asyncio
from solders.pubkey import Pubkey
from asyncstdlib import enumerate
from solana.rpc.websocket_api import connect
from colorama import Fore, Back, init

init(autoreset=True)

async def main():
    
    # Alternatively, use the client as an infinite asynchronous iterator:

    commitment = "confirmed"
    encoding = "jsonParsed"


    count = 0
    async with connect("#") as websocket:
        await websocket.program_subscribe(Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"), commitment=commitment, encoding=encoding)
        first_resp = await websocket.recv()
        subscription_id = first_resp[0].result
        print("Subscribed with id", subscription_id)
        while True:
            next_resp = await websocket.recv()
            count += 1
            msg = next_resp[0]

            #if its a mint and the supply is greater than 1
            if msg.result.value.account.data.parsed["type"] == "mint" and int(msg.result.value.account.data.parsed["info"]["supply"]) > 1:
                if msg.result.value.account.data.parsed["info"].get("extensions"):
                    for extension in msg.result.value.account.data.parsed["info"]["extensions"]:
                        if extension["extension"] == "tokenMetadata":
                            print(Fore.GREEN + "Mint found!" + Fore.RED + extension["state"]["name"])
                    print("--------------------\n")
                else:
                    print("No extensions found\n")

            if count == 100000:
                break
            else:
                if(count % 10 == 0):
                    print("Total messages received:", count)

        await websocket.account_unsubscribe(subscription_id)

        print("Unsubscribed")

asyncio.run(main())
