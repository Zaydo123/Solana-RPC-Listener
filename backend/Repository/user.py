from Model.user import CreateUser
from Config.Connection import prisma_connection

class UserRepository:

    @staticmethod
    async def get_all():
        return await prisma_connection.prisma.user.find_many()
    
    @staticmethod
    async def create_user(data: CreateUser):
        try:
            return await prisma_connection.prisma.user.create(data=data.dict())
        except Exception as e:
            return None
    
    @staticmethod
    async def get_by_id(id: int):
        return await prisma_connection.prisma.user.find_unique(where={"id": id})
    
    @staticmethod
    async def get_by_email(email: str):
        return await prisma_connection.prisma.user.find_unique(where={"email": email})
    
    @staticmethod
    async def update(id: int, user: CreateUser):
        return await prisma_connection.prisma.user.update(where={"id": id}, data=user)
    
    @staticmethod
    async def delete(id: int):
        return await prisma_connection.prisma.user.delete(where={"id": id})
    