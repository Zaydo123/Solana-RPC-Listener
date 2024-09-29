# from fastapi import APIRouter, HTTPException, Query
# from prisma_client import prisma
# from typing import Optional
# import time
# import logging

# router = APIRouter()
# @router.get("/token/{id}")
# async def get_token(id: str, exclude: Optional[str] = Query(None)):
#     try:
#         token = await prisma.token.find_unique(
#             where={'publicKey': id},
#             include={
#                 'prices': True,
#                 'volumes': True,
#                 'largestHolders': {
#                     'include': {
#                         'holders': True
#                     }
#                 }
#             }
#         )
#     except:
#         token = None

#     if not token:
#         raise HTTPException(status_code=404, detail="Token not found")
    
#     result = token.dict()
#     if exclude:
#         for field in exclude.split(","):
#             result.pop(field, None)
    
#     return result

# @router.get("/token")
# async def get_tokens(limit: int = 20, offset: int = 0):
#     try:
#         tokens = await prisma.token.find_many(skip=offset, take=limit)
#     except Exception as e:
#         logging.error(e)
#         tokens = []
    
#     return tokens

# @router.get("/search")
# async def search_tokens(query: str):
#     try:
#         tokens = await prisma.token.find_many(where={'metadata': {'contains': query}})
#     except Exception as e:
#         logging.error(e)
#         tokens = []

#     return tokens
