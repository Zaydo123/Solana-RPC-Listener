from Model.user import User
from Config.Connection import prisma_connection

class UserRepository:
    """
    Repository class for managing user data.
    """

    @staticmethod
    async def get_all():
        """
        Retrieves all users from the database.

        Returns:
            A list of user objects.
        """
        return await prisma_connection.prisma.user.find_many()
    
    @staticmethod
    async def create_user(data: User):
        """
        Creates a new user in the database.

        Args:
            data: The data required to create a new user.

        Returns:
            The created user object, or None if an error occurred.
        """
        try:
            return await prisma_connection.prisma.user.create(data=data.dict())
        except Exception as e:
            print(e)
            return None
    
    @staticmethod
    async def get_by_id(id: int):
        """
        Retrieves a user by their ID.

        Args:
            id: The ID of the user to retrieve.

        Returns:
            The user object with the specified ID, or None if not found.
        """
        return await prisma_connection.prisma.user.find_unique(where={"id": id})
    
    @staticmethod
    async def get_by_email(email: str):
        """
        Retrieves a user by their email.

        Args:
            email: The email of the user to retrieve.

        Returns:
            The user object with the specified email, or None if not found.
        """
        return await prisma_connection.prisma.user.find_unique(where={"email": email})
    
    @staticmethod
    async def update(id: int, user: User):
        """
        Updates a user in the database.

        Args:
            id: The ID of the user to update.
            user: The updated user data.

        Returns:
            The updated user object, or None if an error occurred.
        """
        return await prisma_connection.prisma.user.update(where={"id": id}, data=user)
    
    @staticmethod
    async def delete(id: int):
        """
        Deletes a user from the database.

        Args:
            id: The ID of the user to delete.

        Returns:
            The deleted user object, or None if an error occurred.
        """
        return await prisma_connection.prisma.user.delete(where={"id": id})
    