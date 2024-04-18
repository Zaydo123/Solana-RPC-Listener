from Repository.user import UserRepository
from Model.user import CreateUser
from Library.protect import hash_password

class UserService:
        
        @staticmethod
        async def get_all():
            return await UserRepository.get_all()
        
        @staticmethod
        async def create(data: CreateUser):
            unpacked_data = data.dict()
            unpacked_data['password'] = hash_password(unpacked_data['password'])
            new_user_obj = CreateUser(**unpacked_data)
            return await UserRepository.create_user(new_user_obj)
        
        @staticmethod
        async def get_by_id(id: int):
            return await UserRepository.get_by_id(id)
        
        @staticmethod
        async def get_by_email(email: str):
            return await UserRepository.get_by_email(email)
    
        @staticmethod
        async def update(id: int, data: CreateUser):
            return await UserRepository.update(id, data)
        
        @staticmethod
        async def is_password_correct(email: str, password: str):
            user = await UserRepository.get_by_email(email)
            if user is None:
                return False
            return bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))
        
        @staticmethod
        async def delete(id: int):
            return await UserRepository.delete(id)