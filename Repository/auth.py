from Model.auth import CreateApiKey, GetApiKey
from Config.Connection import prisma_connection

class AuthRepository:

    @staticmethod
    async def get_all():
        return await prisma_connection.prisma.apikey.find_many()
    
    @staticmethod
    async def create_api_key(api_key: CreateApiKey):
        return await prisma_connection.prisma.apikey.create(data={
            "key": api_key.key,
            "userId": api_key.user_id,
            "ipWhitelist": api_key.ip_whitelist,
            "rateLimit": api_key.rate_limit
        })
    
    @staticmethod
    async def get_by_id(id: int):
        return await prisma_connection.prisma.apikey.find_unique(where={"id": id})
    
    @staticmethod
    async def get_by_key(key: str):
        return await prisma_connection.prisma.apikey.find_unique(where={"key": key})
    
    @staticmethod
    async def get_by_user_id(user_id: int):
        return await prisma_connection.prisma.apikey.find_many(where={"userId": user_id})
    
    @staticmethod
    async def update(id: int, api_key: CreateApiKey):
        return await prisma_connection.prisma.apikey.update(where={"id": id}, data={
            "key": api_key.key,
            "userId": api_key.user_id,
            "ipWhitelist": api_key.ip_whitelist,
            "rateLimit": api_key.rate_limit
        })
    
    @staticmethod
    async def delete(id: int):
        return await prisma_connection.prisma.apikey.delete(where={"id": id})