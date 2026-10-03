import os
import google.generativeai as genai
from dotenv import load_dotenv
from .gemini_utils import build_model, generate_with_retry, is_rate_limit_error

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

model = build_model(["gemini-3.8-flash"])

def generate_nutrition_tip(goal: str) -> str:
    prompt = (
        f"Provide a concise, highly effective nutrition and recovery tip specially tailored "
        f"for someone whose main fitness goal is '{goal}'. Format it in Markdown."
    )
    try:
        response = generate_with_retry(model, prompt)
        return response.text
    except Exception as e:
        if is_rate_limit_error(e):
            return (
                "Fallback tip: eat whole foods, include protein in every meal, and sleep 7-8 hours. "
                "Retry in 1-2 minutes for a personalized AI tip."
            )
        return f"Error generating tip: {str(e)}"
