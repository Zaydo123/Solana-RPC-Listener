from typing import Annotated
from fastapi import APIRouter, Path, Query, Body, Depends, HTTPException
from Service.user import UserService
from schema import ResponseSchema
from Model.user import CreateUser, GetUser
from Library.protect import oauth2_scheme

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

@router.post("", response_model=ResponseSchema, response_model_exclude_unset=True, tags=["user"])
async def create_user(data: CreateUser = Body(...)):
    user = await UserService.create(data)
    if user is None:
        raise HTTPException(status_code=400, detail="User already exists or invalid data")

    cleaned_user = user.dict()
    cleaned_user.pop("password")
    cleaned_user.pop("updatedAt")
    cleaned_user.pop("APIKey")

    return ResponseSchema(detail="User created", result=cleaned_user)

@router.get("/me", response_model=ResponseSchema, response_model_exclude_unset=True, tags=["user"])
async def get_me(current_user: Annotated[CreateUser, Depends(oauth2_scheme)]):
    return ResponseSchema(detail="User fetched", result=current_user.dump_model())  
