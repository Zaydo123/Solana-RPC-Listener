from Model.apikey import ApiKey
from Config.Connection import prisma_connection

class ApiKeyRepository:
    """
    Repository class for managing authentication related operations.
    """

    @staticmethod
    async def create_api_key(key: ApiKey):
        """
        Creates a new API key.

        Args:
            key: An instance of ApiKey containing the key details.

        Returns:
            The created API key.
        """
        return await prisma_connection.prisma.apikey.create(data={
            "key": key.key,
            "userId": key.user_id,
            "ipWhitelist": key.ip_whitelist,
            "rateLimit": key.rate_limit
        })

    @staticmethod
    async def get_by_id(id: int):
        """
        Retrieves an API key by its ID.

        Args:
            id: The ID of the API key.

        Returns:
            The API key with the specified ID.
        """
        return await prisma_connection.prisma.apikey.find_unique(where={"id": id})

    @staticmethod
    async def get_by_key(key: str):
        """
        Retrieves an API key by its key value.

        Args:
            key: The key value of the API key.

        Returns:
            The API key with the specified key value.
        """
        return await prisma_connection.prisma.apikey.find_unique(where={"key": key})

    @staticmethod
    async def get_by_user_id(user_id: int):
        """
        Retrieves API keys associated with a user ID.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of API keys associated with the specified user ID.
        """
        return await prisma_connection.prisma.apikey.find_many(where={"userId": user_id})

    @staticmethod
    async def update(id: int, api_key: ApiKey):
        """
        Updates an existing API key.

        Args:
            id: The ID of the API key to update.
            api_key: An instance of ApiKey containing the updated key details.

        Returns:
            The updated API key.
        """
        return await prisma_connection.prisma.apikey.update(where={"id": id}, data={
            "key": api_key.key,
            "userId": api_key.user_id,
            "ipWhitelist": api_key.ip_whitelist,
            "rateLimit": api_key.rate_limit
        })

    @staticmethod
    async def delete(id: int):
        """
        Deletes an API key by its ID.

        Args:
            id: The ID of the API key to delete.

        Returns:
            The deleted API key.
        """
        return await prisma_connection.prisma.apikey.delete(where={"id": id})