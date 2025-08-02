import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import configure

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print("🔥 Using API KEY:", api_key)

configure(api_key=api_key)
print("✅ genai.configure success")

# model = genai.GenerativeModel("gemini-1.5-pro-latest")
model = genai.GenerativeModel("gemini-1.5-flash")


async def check_for_profanity(text: str) -> bool:
    print("🔥 check_for_profanity is running!")
    try:
        prompt = (
            "You are an AI content moderator.\n"
            "Check if the following text contains profanity, insults, hate speech, or inappropriate language.\n"
            "Respond ONLY with one word: 'true' if it should be blocked, 'false' if it is acceptable.\n\n"
            f"Text: {text}"
        )

        response = await model.generate_content_async(prompt)
        result = response.text.strip().lower()
        print("🔍 AI MODERATION RAW RESPONSE:", repr(result))
        return result == "true"
    except Exception as e:
        print("❌ AI moderation error:", e)
        return False
