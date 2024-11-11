# test_database_client.py

import asyncio
from database_client import DatabaseClient

async def test_database():
    db_client = DatabaseClient()
    try:
        # Insert a dummy user need
        await db_client.insert_user_need("Test message", "1234567890", 1)
        
        # Get next unique number
        unique_number = await db_client.get_next_unique_number()
        print(f"Next unique number: {unique_number}")
        
        # Check if a message is processed
        is_processed = await db_client.is_message_processed("dummy_message_id")
        print(f"Is message processed: {is_processed}")
        
        # Insert processed message
        await db_client.insert_processed_message("dummy_message_id", unique_number)
        
        # Check again
        is_processed = await db_client.is_message_processed("dummy_message_id")
        print(f"Is message processed after insertion: {is_processed}")
    except Exception as e:
        print(f"Database test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_database())
