from fastapi import APIRouter, Path, Query, Body, Depends
from Service.apikey import ApiKeyService
from schema import ResponseSchema
from Model.apikey import ApiKey, CreateApiKey
import random, string
from Library.protect import Helpers, oauth2_scheme

router = APIRouter(
    prefix="/api",
    tags=["Api Keys"],
)

#relies on auth
@router.post("/key", response_model=ResponseSchema, response_model_exclude_unset=True, description="Create a new key. Must be authenticated and have the correct permissions.", dependencies=[Depends(oauth2_scheme)])
async def create_key(data: CreateApiKey = Body(...)):

    data["rate_limit"] = 0 # Other rate limit values are not implemented
    data["key"] = Helpers.generate_token()
    data["user_id"] = 0 # Hardcoded for now
    
    k = ApiKey(**data)
    await ApiKeyService.create(k)
    
    return ResponseSchema(detail="Key created", result=k.model_dump())

@router.get("/key/{id}", response_model=ResponseSchema, response_model_exclude_unset=True, description="Get key by id. Must be authenticated and have the correct permissions.", dependencies=[Depends(oauth2_scheme)])
async def get_key(id: int = Path(..., alias="id", title="Key ID", description="The ID of the key to fetch")):
    key = await ApiKeyService.get_by_id(id)
    if key:
        return ResponseSchema(detail="Key found", result=key.model_dump())
    return ResponseSchema(detail="Key not found", result={})
    
@router.get("/keys", response_model=ResponseSchema, response_model_exclude_unset=True, description="Get all user's keys. Must be authenticated and have the correct permissions.", dependencies=[Depends(oauth2_scheme)])
async def get_keys():
    keys = await ApiKeyService.get_by_user_id(oauth2_scheme["user_id"])
    if keys:
        return ResponseSchema(detail="Keys found", result=[key.dict() for key in keys])
    
    return ResponseSchema(detail="No keys found", result=[])

@router.put("/key/disable/{id}", response_model=ResponseSchema, response_model_exclude_unset=True, description="Disable key by id. Must be authenticated and have the correct permissions.", dependencies=[Depends(oauth2_scheme)])
async def disable_key(id: int = Path(..., alias="id", title="Key ID", description="The ID of the key to disable")):
    key = await ApiKeyService.get_by_id(id)
    if key:
        key = await ApiKeyService.update(id, {"enabled": False})
        return ResponseSchema(detail="Key disabled", result=key.dict())
    return ResponseSchema(detail="Key not found")