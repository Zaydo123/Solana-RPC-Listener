from contextlib import asynccontextmanager
from routers.webhooks.mints import router as mint_router
from prisma import Prisma
from colorama import Fore, Style, init, Back
from fastapi import Request, Response, status, FastAPI
from dotenv import load_dotenv

# Module Setup
load_dotenv()
init(autoreset=True)


# ----------------- Prisma -----------------

db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    if not db:
        db = Prisma()
        await db.connect()
        print(Fore.GREEN + "Connected to Prisma : " + str(db.is_connected()))
    yield
    if db:
        await db.disconnect()


# ------------------------------- FastAPI  -------------------------------


print(Fore.BLACK + Back.RED + "Starting webhook server...")
app = FastAPI(name="webhook-server-solana", description="A webhook server for Solana", version="0.0.1", lifespan=lifespan)
app.include_router(mint_router)

public_paths = ["/", "/docs", "/redoc", "/openapi.json"]

# ----------------- Middleware -----------------

@app.middleware("http") 
async def check_api_key(request: Request, call_next):
    if(request.url.path in public_paths):
        return await call_next(request)
    else:
        submitted_key = request.headers.get("X-API-Key")
        api_key = await db.apikey.find_first( where={"key": submitted_key})

        print(api_key)
        if not api_key:
            return Response(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid/Missing API Key")
        
        return await call_next(request)


@app.middleware("http")
async def log_request(request: Request, call_next):
    print(Fore.WHITE + Back.BLACK + f"Incoming request: {request.url.path}")
    response = await call_next(request)
    print(Fore.WHITE + Back.BLACK + f"Outgoing response: {response}")
    return response
    

# ----------------- Basic Routes -----------------

@app.get("/")
async def root():
    return {"message": "Hello World"}

