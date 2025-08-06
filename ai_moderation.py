import os

import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai import configure

from config import PROMPT_FOR_PROFANITY
from loguru import logger

logger.add("loguru/ai_moderation.log")

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
logger.info("Using API KEY:", api_key)

configure(api_key=api_key)
logger.info("genai.configure success")

# model = genai.GenerativeModel("gemini-1.5-pro-latest")
model = genai.GenerativeModel("gemini-1.5-flash")


async def check_for_profanity(text: str) -> bool:
    logger.info("check_for_profanity is running!")
    try:

        response = await model.generate_content_async(PROMPT_FOR_PROFANITY)
        result = response.text.strip().lower()
        logger.info("AI MODERATION RAW RESPONSE:", repr(result))
        return result == "true"
    except Exception as e:
        logger.info("AI moderation error:", e)
        return False
