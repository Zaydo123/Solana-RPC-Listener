from pydantic import BaseModel
from typing import Optional, TypeVar

T = TypeVar('T')

class ResponseSchema(BaseModel):
    status: str
    message: str
    data: Optional[T] = None
    error: Optional[str] = None
    code: Optional[int] = None
    def __init__(self, status: str, message: str, data: Optional[T] = None, error: Optional[str] = None, code: Optional[int] = None):
        self.status = status
        self.message = message
        self.data = data
        self.error = error
        self.code = code
        super().__init__(status=status, message=message, data=data, error=error, code=code)