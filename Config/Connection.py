from prisma import Prisma

class PrismaConnection:

    def __init__(self):
        self.prisma = Prisma()

    async def connect(self):
        await self.prisma.connect()

    async def disconnect(self):
        await self.prisma.disconnect()

    def is_connected(self):
        return self.prisma.is_connected()


prisma_connection = PrismaConnection()