import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
PROMPT_FOR_AUTO_REPLY = os.getenv("PROMPT_FOR_AUTO_REPLY")
PROMPT_FOR_PROFANITY = os.getenv("PROMPT_FOR_PROFANITY")
