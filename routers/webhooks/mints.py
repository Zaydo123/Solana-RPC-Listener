from fastapi import Request, Response, APIRouter

router = APIRouter(
    prefix="/webhooks",
)

@router.post("/")
async def webhook_handler(request: Request, response: Response):
    headers = request.headers
    payload = await request.body()
    msg = f"Received webhook with headers: {headers} and payload: {payload}"
    print(msg)
    return {"status": "success"}

