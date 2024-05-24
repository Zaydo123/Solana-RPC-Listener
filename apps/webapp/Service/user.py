from Repository.user import UserRepository
from Model.user import User
from Library.protect import Helpers
import bcrypt

class UserService:
    """
    Service class for managing user-related operations.
    """

    @staticmethod
    async def get_all():
        """
        Retrieves all users.
        """
        return await UserRepository.get_all()

    @staticmethod
    async def create(data: User):
        """
        Creates a new user.

        Args:
            data (User): The user data.

        Returns:
            The created user object.
        """
        unpacked_data = data.dict()
        unpacked_data['password'] = Helpers.hash_password(unpacked_data['password'])
        new_user_obj = User(**unpacked_data)
        return await UserRepository.create_user(new_user_obj)

    @staticmethod
    async def get_by_id(id: int):
        """
        Retrieves a user by their ID.

        Args:
            id (int): The user ID.

        Returns:
            The user object.
        """
        return await UserRepository.get_by_id(id)

    @staticmethod
    async def get_by_email(email: str):
        """
        Retrieves a user by their email.

        Args:
            email (str): The user email.

        Returns:
            The user object.
        """
        return await UserRepository.get_by_email(email)

    @staticmethod
    async def update(id: int, data: User):
        """
        Updates a user.

        Args:
            id (int): The user ID.
            data (User): The updated user data.

        Returns:
            The updated user object.
        """
        return await UserRepository.update(id, data)

    @staticmethod
    async def is_password_correct(email: str, password: str):
        """
        Checks if the provided password is correct for the given email.

        Args:
            email (str): The user email.
            password (str): The password to check.

        Returns:
            True if the password is correct, False otherwise.
        """
        user = await UserRepository.get_by_email(email)
        if user is None:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))

    @staticmethod
    async def delete(id: int):
        """
        Deletes a user.

        Args:
            id (int): The user ID.

        Returns:
            The deleted user object.
        """
        return await UserRepository.delete(id)
