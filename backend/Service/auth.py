from Repository.auth import AuthRepository
from Model.auth import CreateApiKey

class AuthService:
    
    @staticmethod
    async def get_all():
        return await AuthRepository.get_all()
    
    @staticmethod
    async def create(data: CreateApiKey):
        return await AuthRepository.create_api_key(data)
    
    @staticmethod
    async def get_by_id(id: int):
        return await AuthRepository.get_by_id(id)
    
    @staticmethod
    async def get_by_key(key: str):
        return await AuthRepository.get_by_key(key)
    
    @staticmethod
    async def get_by_user_id(user_id: int):
        return await AuthRepository.get_by_user_id(user_id)

    @staticmethod
    async def is_valid_key(key: str):
        if key is not None and key != "":
            return await AuthRepository.get_by_key(key) is not None
            
        return None
    
    @staticmethod
    async def update(id: int, data: CreateApiKey):
        return await AuthRepository.update(id, data)
    
    
    @staticmethod
    async def delete(id: int):
        return await AuthRepository.delete(id)
