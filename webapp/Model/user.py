from datetime import date, datetime, time, timedelta
from pydantic import BaseModel

class User(BaseModel):
    """
    Represents the data required to create a user.

    Attributes:
        email (str): The email address of the user.
        password (str): The password of the user.
        token (str, optional): The token associated with the user (optional).
    """
    email: str
    password: str

class GetUser(BaseModel):
    """
    Represents the data of a user.

    Attributes:
        id (int): The unique identifier of the user.
        email (str): The email address of the user.
        created_at (str): The timestamp when the user was created.
    """
    id: int
    email: str
    createdAt: datetime
    updatedAt: datetime
