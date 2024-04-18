from pydantic import BaseModel
from typing import Optional, TypeVar

T = TypeVar('T')

class ResponseSchema(BaseModel):
    detail: str
    result: Optional[T] = None
    status: Optional[int] = 200