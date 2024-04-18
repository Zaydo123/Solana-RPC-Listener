import bcrypt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")

def hash_password(password):
    pwd_str = password.encode(encoding="utf-8")
    hashed = bcrypt.hashpw(pwd_str, bcrypt.gensalt())
    return hashed.decode(encoding="utf-8")