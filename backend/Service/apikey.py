from Repository.apikey import ApiKeyRepository
from Model.apikey import ApiKey

class ApiKeyService:
    
    @staticmethod
    async def create(data: ApiKey):
        return await ApiKeyRepository.create_api_key(data)
    
    @staticmethod
    async def get_by_id(id: int):
        return await ApiKeyRepository.get_by_id(id)
    
    @staticmethod
    async def get_by_key(key: str):
        return await ApiKeyRepository.get_by_key(key)
    
    @staticmethod
    async def get_by_user_id(user_id: int):
        return await ApiKeyRepository.get_by_user_id(user_id)

    @staticmethod
    async def is_valid_key(key: str):
        if key is not None and key != "":
            return await ApiKeyRepository.get_by_key(key) is not None
            
        return None
    
    @staticmethod
    async def update(id: int, data: ApiKey):
        return await ApiKeyRepository.update(id, data)
    
    
    @staticmethod
    async def delete(id: int):
        return await ApiKeyRepository.delete(id)
