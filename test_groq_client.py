# test_groq_client.py

import asyncio
from database_client import DatabaseClient
from groq_client import GroqClient

async def test_groq():
    db_client = DatabaseClient()
    groq_client = GroqClient(db_client=db_client)
    message = "I need a new smartphone."
    result = await groq_client.is_product_need_async(message)
    print(f"Is product need: {result}")

if __name__ == "__main__":
    asyncio.run(test_groq())
