from pydantic import BaseModel

class CreateUser(BaseModel):
    email: str
    password: str

class GetUser(BaseModel):
    id: int
    email: str
    created_at: str