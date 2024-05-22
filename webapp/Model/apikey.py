from pydantic import BaseModel

class ApiKey(BaseModel):
    key: str
    user_id: int
    ip_whitelist: list
    rate_limit: int

class CreateApiKey(BaseModel):
    ip_whitelist: list
    
class GetApiKey(BaseModel):
    id: int
    key: str
    user_id: int
    credit: int
    usage: int
    ip_whitelist: list
    rate_limit: int
    active: bool
    created_at: str
    updated_at: str

