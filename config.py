# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')
    CHROME_PROFILE_PATH = os.getenv('CHROME_PROFILE_PATH')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
