# groq_client.py

import logging
from groq import Groq
from config import Config
from database_client import DatabaseClient
import asyncio

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, db_client: DatabaseClient):
        """
        Initializes the GroqClient with the provided DatabaseClient instance.

        Args:
            db_client (DatabaseClient): An instance of DatabaseClient for logging purposes.
        """
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.db_client = db_client
        logger.info("GroqClient initialized successfully.")

    def is_product_need(self, message: str) -> bool: # THIS IS FOR TESTING PURPOSES ONLY , WE DONT USE IN MAIN CODE
        """
        Determines if a message indicates a product-related need using the Groq API.

        Args:
            message (str): The content of the message to classify.

        Returns:
            bool: True if the message is classified as a product need; False otherwise.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a classifier that determines if a message indicates a product-related need. Respond with 'Yes' or 'No' only."
                    },
                    {
                        "role": "user",
                        "content": f"Is the following message a product-related need? Answer only with 'Yes' or 'No'. Message: '{message}'"
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.0,
                max_tokens=10,
                top_p=1,
                stop=["\n"],
                stream=False,
            )
            answer = chat_completion.choices[0].message.content.strip().lower()
            logger.info(f"Groq Classification Result: '{answer}' for message: '{message}'")
            return answer == 'yes'
        except Exception as e:
            logger.error(f"Error during Groq classification: {e}")
            return False

    async def is_product_need_async(self, message_text: str) -> bool:
        """
        Asynchronously determines if a message indicates a product-related need using the Groq API.

        Args:
            message_text (str): The content of the message to classify.

        Returns:
            bool: True if the message is classified as a product need; False otherwise.
        """
        try:
            loop = asyncio.get_running_loop()
            # Run the synchronous method in the default executor (ThreadPoolExecutor)
            result = await loop.run_in_executor(None, self.is_product_need, message_text)
            
            # Log the classification result to the database
            classification = 'Yes' if result else 'No'
            await self.db_client.log_groq_result(message_text, classification)
            
            return result
        except Exception as e:
            logger.error(f"Exception during asynchronous Groq API call: {e}")
            return False
