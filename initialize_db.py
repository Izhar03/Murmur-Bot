# initialize_db.py

import asyncio
import aiosqlite
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE = 'bot_database.db'

async def initialize_db():
    async with aiosqlite.connect(DATABASE) as db:
        # Enable foreign key support
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Create processed_messages table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id TEXT PRIMARY KEY,
                unique_number INTEGER NOT NULL
            );
        """)
        logger.info("Created table: processed_messages")
        
        # Create user_needs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_needs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT NOT NULL,
                contact TEXT NOT NULL,
                unique_number INTEGER NOT NULL,
                FOREIGN KEY (unique_number) REFERENCES processed_messages(unique_number)
            );
        """)
        logger.info("Created table: user_needs")
        
        # Create a sequence table for unique_number
        await db.execute("""
            CREATE TABLE IF NOT EXISTS message_unique_number_seq (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                next_unique_number INTEGER NOT NULL
            );
        """)
        logger.info("Created table: message_unique_number_seq")
        
        # Initialize the sequence if it's empty
        cursor = await db.execute("SELECT COUNT(*) FROM message_unique_number_seq;")
        count = await cursor.fetchone()
        if count[0] == 0:
            await db.execute("INSERT INTO message_unique_number_seq (id, next_unique_number) VALUES (1, 1);")
            logger.info("Initialized message_unique_number_seq with next_unique_number = 1")
        
        # Create logging tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groq_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT NOT NULL,
                classification TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Created table: groq_logs")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS perplexity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                contact TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Created table: perplexity_logs")
        
        
        # Add final_response_table (for affiliate link V2)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS final_response_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_number INTEGER NOT NULL,
                contact TEXT NOT NULL,
                message_text TEXT NOT NULL,
                generated_response TEXT NOT NULL,
                affiliate_link TEXT,
                status TEXT DEFAULT 'pending', -- 'pending', 'affiliate_added', 'sent'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (unique_number) REFERENCES processed_messages(unique_number)
            );
        """)
        logger.info("Created table: final_response_table")
        
        await db.commit()

if __name__ == "__main__":
    asyncio.run(initialize_db())
