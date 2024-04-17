from Repository.auth import AuthRepository

class AuthService:
    
    @staticmethod
    async def get_all():
        return await AuthRepository.get_all()
    
    @staticmethod
    async def create(data: dict):
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
    async def update(id: int, auth: str):
        return await AuthRepository.update(id, auth)
    
    @staticmethod
    async def delete(id: int):
        return await AuthRepository.delete(id)
