# perplexity_client.py

import logging
import aiohttp
from config import Config
import asyncio
from database_client import DatabaseClient  # Import the DatabaseClient

logger = logging.getLogger(__name__)

class PerplexityClient:
    def __init__(self, db_client: DatabaseClient):
        self.api_key = Config.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"  # Replace with the actual Perplexity API base URL
        self.db_client = db_client  # Store the DatabaseClient instance

    async def get_response_async(self, query: str, contact: str, unique_number: int) -> str:
        """
        Asynchronously fetches product information including Indian product links and
        Reddit reviews using the Perplexity API based on the user's query and stores the response for
        affiliate link integration.
        
        Args:
            query (str): The query string provided by the user (e.g., "vitamin c serum").
            contact (str): The contact details extracted from the message metadata.
            unique_number (int): The unique identifier for the message.
        
        Returns:
            str: Acknowledgment message or status.
        """
        model = "llama-3.1-sonar-small-128k-online"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant helping a user find a specific product with reviews. "
                    "The user needs a product available in India, and you should provide only one product link "
                    "from either Amazon India, Myntra, Flipkart, or Nykaa. Additionally, provide exactly two positive Reddit reviews "
                    "and two negative Reddit reviews for this product.\n\n"
                    "You will be given the following inputs:\n\n"
                    "- **Product Details:**\n"
                    "  - Product Name\n"
                    "  - Key Features or Ingredients\n"
                    "  - Product Link\n"
                    "- **Positive Reviews:** A list of positive feedback from people who have used the product.\n"
                    "- **Negative Reviews:** A list of any negative feedback or cautions.\n\n"
                    "**Your Task:**\n\n"
                    "Compose a concise, friendly WhatsApp message recommending the product to someone. The message should:\n\n"
                    "- Start with a casual greeting.\n"
                    "- Introduce the product and highlight its key features.\n"
                    "- Mention positive feedback using phrases like \"Someone I suggested this to told me...\"\n"
                    "- Briefly note any cautions from the negative feedback with gentle phrases like \"Just a heads up...\"\n"
                    "- Include the product link at the end.\n"
                    "- Keep the tone conversational and the message suitable for WhatsApp—short and easy to read.\n"
                    "- Preserve all important information and semantic meaning from the inputs.\n\n"
                    "**Example Format:**\n\n"
                    "Hey! Just wanted to recommend [Product Name] with [Key Features]. Someone I suggested it to noticed [Positive Feedback 1]—[additional details if necessary]. Another person said [Positive Feedback 2], which is great for [specific needs].\n\n"
                    "Just a heads up, some people [mention any negative feedback].\n\n"
                    "If you're interested, here's the link: [Product Link]. Hope it helps!"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"This is a user's need: {query}.\n\n"
                    f"Please provide a WhatsApp message as per the instructions above, including an Indian product link from Amazon India, Myntra, Flipkart, or Nykaa, and incorporating exactly two positive and two negative Reddit reviews.\n\n"
                    f"Use this format:\n\n"
                    f"Hey, I saw your need {contact}, here is the solution to your need: <response>\n\n"
                    f"where {contact} is the contact number and <response> is the message to the user."
                ),
            },
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7,  # Adjust temperature as needed
            "top_p": 1,
            "n": 1,
            "stream": False
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/chat/completions", json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        recommendation = data['choices'][0]['message']['content'].strip()
                        logger.info(f"Perplexity Recommendation: {recommendation}")
                        
                        # Insert recommendation into final_response_table with unique_number
                        await self.db_client.insert_final_response(unique_number, contact, query, recommendation)
                        
                        return "Response generated and awaiting affiliate link."
                    else:
                        logger.error(f"Perplexity API error: {resp.status} - {resp.reason}")
                        return "Sorry, I couldn't retrieve the product information at this time."
            
            except Exception as e:
                logger.error(f"Exception during Perplexity API call: {e}")
                return "Sorry, I couldn't retrieve the product information at this time."

