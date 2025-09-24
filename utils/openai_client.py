from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# WIndexAI API Configuration
WINDEXAI_API_KEY = os.getenv("WINDEXAI_API_KEY", "your-openai-api-key-here")

# Initialize OpenAI client
windexai_client = OpenAI(api_key=WINDEXAI_API_KEY)

def get_openai_client() -> OpenAI:
    """Get OpenAI client instance"""
    return windexai_client
