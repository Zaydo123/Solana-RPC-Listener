from fastapi import APIRouter, Path, Query, Body
from Service.auth import AuthService
from schema import ResponseSchema
from Model.auth import CreateApiKey
import random, string

router = APIRouter(
    prefix="/api",
    tags=["auth"],
)

@router.post("/key", response_model=ResponseSchema, response_model_exclude_unset=True, description="Create a new key. Must be authenticated and have the correct permissions.")
async def create_key(data: dict = Body(..., title="Whitelist", description="The IP whitelist for the key")):

    generated_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    data["rate_limit"] = 0 # Other rate limit values are not implemented
    data["key"] = generated_key
    data["user_id"] = 0 # Hardcoded for now
    
    k = CreateApiKey(**data)
    await AuthService.create(k)
    
    return ResponseSchema(detail="Key created", result=k.model_dump())

@router.get("/key/{id}", response_model=ResponseSchema, response_model_exclude_unset=True, description="Get key by id. Must be authenticated and have the correct permissions.")
async def get_key(id: int = Path(..., alias="id", title="Key ID", description="The ID of the key to fetch")):
    key = await AuthService.get_by_id(id)
    if key:
        return ResponseSchema(detail="Key found", result=key.model_dump())
    return ResponseSchema(detail="Key not found", result={})
    
@router.get("/keys", response_model=ResponseSchema, response_model_exclude_unset=True, description="Get all user's keys. Must be authenticated and have the correct permissions.")
async def get_keys():
    keys = await AuthService.get_all()
    if keys:
        return ResponseSchema(detail="Keys found", result=[key.dict() for key in keys])
    
    return ResponseSchema(detail="No keys found", result=[])

@router.put("/key/disable/{id}", response_model=ResponseSchema, response_model_exclude_unset=True, description="Disable key by id. Must be authenticated and have the correct permissions.")
async def disable_key(id: int = Path(..., alias="id", title="Key ID", description="The ID of the key to disable")):
    key = await AuthService.get_by_id(id)
    if key:
        key = await AuthService.update(id, {"enabled": False})
        return ResponseSchema(detail="Key disabled", result=key.dict())
    return ResponseSchema(detail="Key not found")