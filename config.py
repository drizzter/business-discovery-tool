"""Configuration loader."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://three-mistress-opera-locations.trycloudflare.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-_-_6iOA9bmW5nRx3f9CKKw")
