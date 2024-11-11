# database_client.py

import logging
import aiosqlite
import asyncio

logger = logging.getLogger(__name__)

DATABASE = 'bot_database.db'

class DatabaseClient:
    def __init__(self):
        self.db_path = DATABASE

    async def insert_user_need(self, message_text: str, contact: str, unique_number: int):
        """
        Inserts a user need into the 'user_needs' table.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO user_needs (message_text, contact, unique_number)
                    VALUES (?, ?, ?);
                """, (message_text, contact, unique_number))
                await db.commit()
                logger.info(f"Inserted user need: '{message_text}', '{contact}', '{unique_number}'")
        except Exception as e:
            logger.error(f"Error inserting user need: {e}")

    async def get_next_unique_number(self) -> int:
        """
        Retrieves and increments the next unique number from the sequence.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("BEGIN;")
                cursor = await db.execute("""
                    SELECT next_unique_number FROM message_unique_number_seq WHERE id = 1;
                """)
                row = await cursor.fetchone()
                if row:
                    unique_number = row[0]
                    await db.execute("""
                        UPDATE message_unique_number_seq SET next_unique_number = next_unique_number + 1 WHERE id = 1;
                    """)
                    await db.commit()
                    logger.info(f"Retrieved next unique number: {unique_number}")
                    return unique_number
                else:
                    raise Exception("Sequence not initialized.")
        except Exception as e:
            logger.error(f"Error retrieving unique number: {e}")
            raise

    async def insert_processed_message(self, message_id: str, unique_number: int):
        """
        Inserts a processed message into the 'processed_messages' table.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO processed_messages (message_id, unique_number)
                    VALUES (?, ?);
                """, (message_id, unique_number))
                await db.commit()
                logger.info(f"Marked message as processed: '{message_id}' with unique number: {unique_number}'")
        except aiosqlite.IntegrityError:
            logger.warning(f"Message '{message_id}' is already processed.")
        except Exception as e:
            logger.error(f"Error marking message as processed: {e}")

    async def is_message_processed(self, message_id: str) -> bool:
        """
        Checks if a message has already been processed.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT message_id FROM processed_messages WHERE message_id = ?;
                """, (message_id,))
                row = await cursor.fetchone()
                is_processed = row is not None
                logger.debug(f"Message '{message_id}' processed: {is_processed}")
                return is_processed
        except Exception as e:
            logger.error(f"Error checking if message is processed: {e}")
            return False

    # New logging methods for API clients

    async def log_groq_result(self, message_text: str, classification: str):
        """
        Logs the result of the Groq classification.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS groq_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_text TEXT NOT NULL,
                        classification TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                await db.execute("""
                    INSERT INTO groq_logs (message_text, classification)
                    VALUES (?, ?);
                """, (message_text, classification))
                await db.commit()
                logger.info(f"Logged Groq classification: '{classification}' for message: '{message_text}'")
        except Exception as e:
            logger.error(f"Error logging Groq result: {e}")

    async def log_perplexity_response(self, query: str, contact: str, response: str):
        """
        Logs the response from the Perplexity API.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS perplexity_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        contact TEXT NOT NULL,
                        response TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                await db.execute("""
                    INSERT INTO perplexity_logs (query, contact, response)
                    VALUES (?, ?, ?);
                """, (query, contact, response))
                await db.commit()
                logger.info(f"Logged Perplexity response for query: '{query}' and contact: '{contact}'")
        except Exception as e:
            logger.error(f"Error logging Perplexity response: {e}")
    
    async def insert_final_response(self, unique_number: int, contact: str,
        message_text: str, generated_response: str):
        """
        Inserts a generated response into the 'final_response_table'.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO final_response_table (unique_number, contact,
                    message_text, generated_response)
                    VALUES (?, ?, ?, ?); """, 
                (unique_number, contact, message_text, generated_response))
                await db.commit()
            logger.info(f"Inserted final response for unique number: {unique_number}")
        except Exception as e:
            logger.error(f"Error inserting final response: {e}")
            

    async def update_affiliate_link(self, unique_number: int, affiliate_link: str):
        """
        Updates the affiliate link and status for a given unique number in
        'final_response_table'.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE final_response_table
                    SET affiliate_link = ?, status = 'affiliate_added', updated_at = CURRENT_TIMESTAMP
                    WHERE unique_number = ? AND status = 'pending';
                """, (affiliate_link, unique_number))
                await db.commit()
            logger.info(f"Updated affiliate link for unique number: {unique_number}")
        except Exception as e:
            logger.error(f"Error updating affiliate link: {e}")
            

    async def fetch_pending_affiliates(self):
        """
        Retrieves all entries from 'final_response_table' where affiliate_link is
        pending.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT unique_number, generated_response
                    FROM final_response_table
                    WHERE status = 'affiliate_added' AND affiliate_link IS NOT NULL;
                """)
                rows = await cursor.fetchall()
                return rows
        except Exception as e:
            logger.error(f"Error fetching pending affiliates: {e}")
            return []

    async def mark_as_sent(self, unique_number: int):
        """
        Marks the entry in 'final_response_table' as sent.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE final_response_table
                    SET status = 'sent', updated_at = CURRENT_TIMESTAMP
                    WHERE unique_number = ?;
                """, (unique_number,))
                await db.commit()
            logger.info(f"Marked unique number {unique_number} as sent.")
        except Exception as e:
            logger.error(f"Error marking as sent: {e}")
            
    async def delete_pending_response(self, unique_number):
        """
        Deletes a pending response based on unique_number.
        """
        query = "DELETE FROM final_response_table WHERE unique_number = ?"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, (unique_number,))
            await db.commit()
   
