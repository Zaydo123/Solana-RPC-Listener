from typing import Annotated
from fastapi import APIRouter, Path, Query, Body, Depends, HTTPException
from Service.user import UserService
from schema import ResponseSchema
from Model.user import User, GetUser
from Library.protect import Helpers, oauth2_scheme

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

@router.post("/register", response_model=ResponseSchema, response_model_exclude_unset=True, tags=["user"])
async def create_user(data: User = Body(...)):
    user = await UserService.create(data)
    if user is None:
        raise HTTPException(status_code=400, detail="User already exists or invalid data")

    cleaned_user = user.dict()
    cleaned_user.pop("password")
    cleaned_user.pop("updatedAt")
    cleaned_user.pop("APIKey")

    return ResponseSchema(detail="User created", result=cleaned_user)

@router.post("/auth")
async def login_for_access_token(supposed_user: User = Body(...)):
    user = await UserService.get_by_email(supposed_user.email)
    user = user.dict()
    if user is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not await UserService.is_password_correct(supposed_user.email, supposed_user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    jwt_user_info = GetUser(**user)
    print(jwt_user_info)

    token = Helpers.create_access_token(jwt_user_info)

    return ResponseSchema(detail="Token created", result={"token": token})


@router.get("/me", response_model=ResponseSchema, response_model_exclude_unset=True, tags=["user"])
async def get_me(current_user: Annotated[User, Depends(oauth2_scheme)]):
    return ResponseSchema(detail="User fetched", result=current_user.dump_model())  



#@app.post("/user/token", response_model=ResponseSchema, response_model_exclude_unset=True, tags=["user"])
