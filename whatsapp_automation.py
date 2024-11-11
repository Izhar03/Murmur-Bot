# whatsapp_automation.py

import aiosqlite
import asyncio
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from database_client import DatabaseClient
from perplexity_client import PerplexityClient
from groq_client import GroqClient
import re
import hashlib
from config import Config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WhatsAppBot:
    def __init__(self, group_name: str):
        self.group_name = group_name
        self.driver = self.init_driver()
        self.actions = ActionChains(self.driver)
        self.database_client = DatabaseClient()
        self.groq_client = GroqClient(db_client=self.database_client)
        self.perplexity_client = PerplexityClient(db_client=self.database_client)

        # Initialize asyncio queues
        self.incoming_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()

    def init_driver(self):
        chrome_driver_path = Config.CHROME_DRIVER_PATH  
        chrome_profile_path = Config.CHROME_PROFILE_PATH  

        options = Options()
        options.add_argument(f"user-data-dir={chrome_profile_path}")
        options.add_argument("--disable-dev-shm-usage")  # Overcomes limited resource problems
        options.add_argument("--no-sandbox")  # Bypass OS security model
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        try:
            service = Service(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            driver.maximize_window()
            logger.info("ChromeDriver initialized successfully.")
            return driver
        except Exception as e:
            logger.error(f"Error initializing ChromeDriver: {e}")
            raise
        
    def remove_urls(self,text: str) -> str:
        """
        Removes all URLs from the given text.

        Args:
            text (str): The text from which URLs should be removed.

        Returns:
            str: Text without URLs.
        """
        url_pattern = re.compile(r'http\S+|www\.\S+')
        return url_pattern.sub('', text)

    def open_whatsapp_web(self):
        try:
            self.driver.get("https://web.whatsapp.com/")
            logger.info("WhatsApp Web opened. Please scan the QR code if not already logged in.")
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id="side"]'))
            )
            logger.info("Logged into WhatsApp Web successfully.")
        except TimeoutException:
            logger.error("Timeout while waiting for WhatsApp Web to load. Ensure QR code is scanned.")
            self.driver.quit()
            raise
        except Exception as e:
            logger.error(f"Error opening WhatsApp Web: {e}")
            self.driver.quit()
            raise

    def select_group(self):
        try:
            search_box = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="3"]'))
            )
            search_box.clear()
            time.sleep(1)
            search_box.send_keys(self.group_name)
            logger.info(f"Searching for group: {self.group_name}")
            time.sleep(2)
            group_title = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//span[@title="{self.group_name}"]'))
            )
            group_title.click()
            logger.info(f"Selected group: {self.group_name}")
            time.sleep(3)  # Allow time for messages to load
        except TimeoutException:
            logger.error(f"Timeout while selecting group: {self.group_name}. Ensure the group name is correct.")
            self.driver.quit()
            raise
        except Exception as e:
            logger.error(f"Error selecting group: {e}")
            self.driver.quit()
            raise

    def extract_contact_details_from_metadata(self, metadata):
        """
        Extracts contact details from the message metadata.
        
        Args:
            metadata (str): The raw metadata string from WhatsApp Web.
        
        Returns:
            str: The contact details extracted.
        """
        # Regex pattern to extract text between "] " and ": "
        match = re.search(r'] (.+?):', metadata)
        if match:
            return match.group(1)
        return "unknown_contact"

    def extract_timestamp_from_metadata(self, metadata):
        """
        Extracts timestamp from the message metadata.
        
        Args:
            metadata (str): The raw metadata string from WhatsApp Web.
        
        Returns:
            str: The timestamp extracted.
        """
        # Regex pattern to extract text between "[" and "]"
        match = re.search(r'\[(.*?)\]', metadata)
        if match:
            return match.group(1)
        return "unknown_time"

    def generate_unique_message_id(self, contact: str, timestamp: str, message_text: str) -> str:
        """
        Generates a unique identifier for a message using SHA-256 hash.

        Args:
            contact (str): Contact details extracted from metadata.
            timestamp (str): Timestamp extracted from metadata.
            message_text (str): The text content of the message.

        Returns:
            str: A unique hash string.
        """
        unique_string = f"{contact}_{timestamp}_{message_text}"
        message_hash = hashlib.sha256(unique_string.encode()).hexdigest()
        return message_hash

    async def extract_new_messages(self): 
        """
        Extracts messages from group chat asynchronously and adds all messages without filtering to incoming_queue.
        """
        while True:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id="main"]'))
                )

                # Scroll to bottom to load latest messages
                try:
                    scroll_to_bottom_button = self.driver.find_element(By.XPATH, '//div[@aria-label="Scroll to bottom"]')
                    scroll_to_bottom_button.click()
                except NoSuchElementException:
                    pass

                messages = self.driver.find_elements(By.CSS_SELECTOR, "div.message-in")  # Collect the most recent messages by scrolling to bottom

                for message in messages:
                    try:
                        # A message = metadata + message_text, so extract both separately
                        metadata = message.find_element(By.XPATH, './/div[contains(@class, "copyable-text")]').get_attribute('data-pre-plain-text')
                        message_text = message.find_element(By.CSS_SELECTOR, 'span.selectable-text').text

                        # Extract contact details and timestamp from metadata using predefined functions
                        contact = self.extract_contact_details_from_metadata(metadata)
                        timestamp = self.extract_timestamp_from_metadata(metadata)

                        # Generate unique message ID
                        message_id = self.generate_unique_message_id(contact, timestamp, message_text)

                        if not await self.database_client.is_message_processed(message_id):
                            # Get the next unique number from the sequence
                            unique_number = await self.database_client.get_next_unique_number()

                            # Insert the processed message into the database since its unique number is made so it can't be reprocessed 
                            await self.database_client.insert_processed_message(message_id, unique_number)

                            # Queue the message for further processing into incoming_queue 
                            await self.incoming_queue.put((contact, message_text, unique_number))
                            logger.info(f"Queued new message: '{message_text}' with Unique Number: {unique_number}")
                    except StaleElementReferenceException:
                        continue  # Message no longer in DOM
                    except NoSuchElementException:
                        continue  # Required elements not found
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                await asyncio.sleep(5)  # Polling interval
            except Exception as e:
                logger.error(f"Error extracting new messages: {e}")
                await asyncio.sleep(5)

    async def process_incoming_messages(self): 
        """
        Processes messages from incoming_queue: checks if the message indicates a product need and, if so, queues it for response.
        """
        while True:
            try:
                contact, message_text, unique_number = await self.incoming_queue.get()
                await self.log_user_need(contact, message_text, unique_number)

                is_product_need = await self.groq_client.is_product_need_async(message_text)
                if is_product_need:
                    await self.response_queue.put((unique_number,contact, message_text))
                    logger.info(f"Message categorized as product need: '{message_text}'")
                
                self.incoming_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing incoming message: {e}")

    async def give_product_need_response_to_user(self): 
        """
        Processes responses from response_queue: gets a response from Perplexity and sends it to the group chat.
        """
        while True:
            try:
                unique_number, contact, message_text = await self.response_queue.get()
                response = await self.perplexity_client.get_response_async(message_text, contact,unique_number)
                await self.send_response(response)
                logger.info(f"Developer Log - Response for unique number {unique_number}: {response}")
                self.response_queue.task_done()
            except Exception as e:
                logger.error(f"Error giving product need response: {e}")

    async def send_response(self, response: str):
        """
        Sends the response to the WhatsApp group chat.
        """
        try:
            input_box = self.driver.find_element(By.XPATH, '//div[@aria-placeholder="Type a message"]')
            input_box.send_keys(response + Keys.ENTER)
            logger.info(f"Sent response: {response}")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            
    async def log_user_need(self, contact: str, message_text: str, unique_number: int):
        """
        Logs the user's need into the database.
        """
        try:
            await self.database_client.insert_user_need(message_text, contact, unique_number)
            logger.info(f"Logged user need: '{message_text}','{contact}','{unique_number}'")
        except Exception as e:
            logger.error(f"Error logging user need for '{message_text}','{contact}','{unique_number}': {e}")
                       
    async def send_final_responses(self):
        while True:
            try:
                pending_responses = await self.database_client.fetch_pending_affiliates()
                for entry in pending_responses:
                    unique_number, generated_response = entry
 
                    async with aiosqlite.connect(self.database_client.db_path) as db:
                        cursor = await db.execute("""
                            SELECT affiliate_link, contact
                            FROM final_response_table
                            WHERE unique_number = ?;
                        """, (unique_number,))
                        row = await cursor.fetchone()

                        if row:
                            affiliate_link, contact = row

                            processed_generated_response = self.remove_urls(generated_response).strip()
                            final_response = f"{processed_generated_response}\nProduct Link: {affiliate_link}"

                            await self.send_response(final_response)
                            await self.database_client.mark_as_sent(unique_number)
                            logger.info(f"Sent final response for unique number: {unique_number}")

                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error sending final responses: {e}")
                await asyncio.sleep(10)

    async def run(self):
            try:
                # Open WhatsApp Web and select the group
                self.open_whatsapp_web()
                self.select_group()

                # Start asynchronous tasks
                tasks = [
                    # Extract new messages from the queue
                    asyncio.create_task(self.extract_new_messages()),

                    # Process incoming messages and send them to the response queue
                    asyncio.create_task(self.process_incoming_messages()),

                    # Generate product need responses and send to the group chat
                    asyncio.create_task(self.give_product_need_response_to_user()),

                    # Periodically check and send final responses with affiliate links
                    asyncio.create_task(self.send_final_responses())
                ]

                # Run all tasks concurrently
                await asyncio.gather(*tasks)

            except Exception as e:
                logger.error(f"Error in run method: {e}")
                self.driver.quit()
                raise


if __name__ == "__main__":
    group_name = "affbot"  
    bot = WhatsAppBot(group_name)
    asyncio.run(bot.run())
