from fastapi import Request, Response, status, FastAPI
from Config.Connection import prisma_connection
from contextlib import asynccontextmanager
from colorama import Fore, Style, init, Back
from typing import Annotated
#from dotenv import load_dotenv
#import os
#import sys

#----------------- Routes -----------------

from Controller.apiKey import router as apikey_router
from Controller.user import router as user_router

#-----------------        -----------------

#OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="/token/find") -> This is used for authentication later on
#load_dotenv()
init(autoreset=True)

# ----------------- Messages -----------------

PRISMA_CONNECTING_MESSAGE    = Fore.BLACK + Back.RED + "[!] Starting Prisma connection..."
PRISMA_CONNECTED_MESSAGE     = Fore.GREEN +            "[✓] Connected with Prisma"
PRISMA_DISCONNECTING_MESSAGE = Fore.BLACK + Back.RED + "[!] Closing Prisma connection..."
PRISMA_DISCONNECTED_MESSAGE  = Fore.RED +              "[X] Disconnected from Prisma"
FASTAPI_STARTING_MESSAGE     = Fore.BLACK + Back.RED + "[!] Starting FastAPI server..."

# ----------------- Prisma -----------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    print(PRISMA_CONNECTING_MESSAGE)
    await prisma_connection.connect()

    if prisma_connection.is_connected() == False:
        print(Fore.RED + "[X] Failed to connect to Database")
        raise Exception("Failed to connect to Database server")
    
    print(PRISMA_CONNECTED_MESSAGE)

    yield

    print(PRISMA_DISCONNECTING_MESSAGE)
    await prisma_connection.disconnect()
    print(PRISMA_DISCONNECTED_MESSAGE)

# ------------------------------- FastAPI  -------------------------------

print(FASTAPI_STARTING_MESSAGE)
app = FastAPI(name="webhook-server-solana", description="A webhook server for Solana", version="0.0.1", lifespan=lifespan)

app.include_router(apikey_router)
app.include_router(user_router)


# ----------------- Basic Routes -----------------

@app.get("/")
async def root():
    return {"message": "Hello World"}
