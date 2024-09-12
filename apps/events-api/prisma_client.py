# prisma_client.py
from prisma import Prisma
import asyncio
import logging
prisma = Prisma(log_queries=True)

async def connect_prisma_with_retry(retries=3, delay=2):
    for attempt in range(retries):
        try:
            await prisma.connect()
            if prisma.is_connected():
                logging.info("Connected to Prisma")
                return
        except Exception as e:
            logging.fatal(f"Attempt {attempt + 1}: Failed to connect to Prisma: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    raise ConnectionError("Failed to connect to Prisma after multiple attempts.")
