from fastapi import APIRouter, Path, Query
from schema import ResponseSchema
from Service.auth import AuthService
from Model.auth import CreateApiKey

router = APIRouter(
    prefix="/api/auth",
)

@router.post("/key", response_model=ResponseSchema, response_model_exclude_unset=True, description="Create a new key. Must be authenticated and have the correct permissions.")
async def create_key(whitelist: str = Query(..., title="Whitelist", description="The IP whitelist for this key"), data: CreateApiKey = None):
    """
    Create a new key. Must be authenticated and have the correct permissions.
    """
    key = await AuthService.create(data)
    return ResponseSchema(status="success", message="Key created", data=key.dict())

@router.get("/key/{id}", response_model=ResponseSchema, response_model_exclude_unset=True, description="Get key by id. Must be authenticated and have the correct permissions.")
async def get_key(id: int = Path(..., alias="id", title="Key ID", description="The ID of the key to fetch")):
    """
    Get key by id. Must be authenticated and have the correct permissions.
    """
    key = await AuthService.get_by_id(id)
    if key:
        return ResponseSchema(status="success", message="Key found", data=key.dict())
    return ResponseSchema(status="error", message="Key not found")
    
@router.get("/keys", response_model=ResponseSchema, response_model_exclude_unset=True, description="Get all user's keys. Must be authenticated and have the correct permissions.")
async def get_keys():
    """
    Get all user's keys. Must be authenticated and have the correct permissions
    """
    keys = await AuthService.get_all()
    
    if keys:
        return ResponseSchema(status="success", message="Keys found", data=[key.model_dump() for key in keys])
    return ResponseSchema(status="error", message="Keys not found")

