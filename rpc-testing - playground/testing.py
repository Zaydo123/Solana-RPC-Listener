from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
import solders
from solders.signature import Signature
from solders.pubkey import Pubkey
from colorama import Fore, init
import json, time, asyncio, sys

client = AsyncClient("https://api.mainnet-beta.solana.com")

# raydium pubkey 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8
raydium_key = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")


async def func():
    sigs = []
    all_sigs = await client.get_signatures_for_address(Pubkey.from_string("HToXKDG27DkuR6TLvpFNgBLiHBEsfrE4ruqwtHUDJ1ML"), limit=10)
    
    print(all_sigs.to_json())

    for sig in all_sigs.to_json():
        sigs.append(sig) if sig["err"] == None else None
        
asyncio.run(func())