from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from Model.user import GetUser
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from dotenv import load_dotenv
import random, string
import bcrypt
import os, json

load_dotenv("../.env")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/auth")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Helpers:

    @staticmethod
    def generate_token(): # Generate a random 32 character token for API Key
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    @staticmethod
    def hash_password(password):
        pwd_str = password.encode(encoding="utf-8")
        hashed = bcrypt.hashpw(pwd_str, bcrypt.gensalt())
        return hashed.decode(encoding="utf-8")

    @staticmethod
    def create_access_token(data: GetUser):
        to_encode = data.dict().copy()
        expire = datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode["createdAt"] = to_encode["createdAt"].timestamp()
        to_encode["updatedAt"] = to_encode["updatedAt"].timestamp()
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
        