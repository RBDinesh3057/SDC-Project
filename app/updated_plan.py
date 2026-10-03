import os
import google.generativeai as genai
from dotenv import load_dotenv
from .gemini_utils import build_model, generate_with_retry, is_rate_limit_error

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

model = build_model(["gemini-3.8-flash"])

def get_updated_plan(original_plan: str, feedback: str) -> str:
    prompt = (
        f"Here is an original 7-day workout plan:\n\n{original_plan}\n\n"
        f"The user has provided the following feedback to adjust the plan: '{feedback}'\n\n"
        f"Please rewrite and provide the complete updated 7-day workout plan incorporating "
        f"this feedback. Ensure it still contains warm up, exercises with sets/reps, and cooldown "
        f"for every day, structured nicely in Markdown."
    )
    try:
        response = generate_with_retry(model, prompt)
        return response.text
    except Exception as e:
        if is_rate_limit_error(e):
            return (
                original_plan
                + "\n\n---\n"
                + "_Note: AI update is temporarily rate-limited (HTTP 429). "
                + "Please retry in 1-2 minutes for a personalized update._"
            )
        return f"Error updating plan: {str(e)}"
