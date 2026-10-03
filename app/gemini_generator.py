import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .gemini_utils import (
    build_model,
    generate_with_retry,
    is_model_not_found_error,
    is_rate_limit_error,
)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

model = build_model(["gemini-3.8-flash"])


def _fallback_plan(goal: str, intensity: str) -> str:
    return (
        "## 7-Day Backup Workout Plan\n\n"
        f"This plan is a temporary fallback for goal: **{goal}** at **{intensity}** intensity.\n\n"
        "### Day 1 (Full Body)\n"
        "- Warm up: 8 min brisk walk + arm circles\n"
        "- Main: Squats 3x12, Push-ups 3x10, Glute bridges 3x15, Plank 3x30s\n"
        "- Cooldown: Hamstring + chest stretch 5 min\n\n"
        "### Day 2 (Cardio + Core)\n"
        "- Warm up: 5 min light jog\n"
        "- Main: 25 min brisk cardio, Bicycle crunches 3x20, Side plank 3x20s/side\n"
        "- Cooldown: Hip flexor stretch 5 min\n\n"
        "### Day 3 (Lower Body)\n"
        "- Warm up: Dynamic leg swings 5 min\n"
        "- Main: Lunges 3x12/leg, Step-ups 3x12/leg, Calf raises 3x20\n"
        "- Cooldown: Quad + calf stretch 5 min\n\n"
        "### Day 4 (Recovery)\n"
        "- Warm up: Easy walk 10 min\n"
        "- Main: Mobility flow 20 min + light yoga\n"
        "- Cooldown: Deep breathing 5 min\n\n"
        "### Day 5 (Upper Body)\n"
        "- Warm up: Shoulder rolls + band pull-aparts 5 min\n"
        "- Main: Incline push-ups 3x12, Rows 3x12, Overhead press 3x10\n"
        "- Cooldown: Shoulder + tricep stretch 5 min\n\n"
        "### Day 6 (Conditioning)\n"
        "- Warm up: Jumping jacks 3 min\n"
        "- Main: 6 rounds (30s work / 30s rest): squats, mountain climbers, plank\n"
        "- Cooldown: Full body stretch 8 min\n\n"
        "### Day 7 (Active Rest)\n"
        "- Warm up: Gentle walk 5 min\n"
        "- Main: 20-30 min light activity (walk, cycle, or yoga)\n"
        "- Cooldown: Stretch and hydration\n"
    )

def generate_plan_and_tip(age: int, weight: int, goal: str, intensity: str) -> dict:
    prompt = (
        f"Generate a structured 7-day workout plan for a {age}-year-old weighing {weight} kg "
        f"with a fitness goal to '{goal}' at a '{intensity}' intensity level.\n\n"
        f"For each of the 7 days, you MUST include:\n"
        f"- Warm up\n"
        f"- Main exercises with sets and reps\n"
        f"- Cooldown tips\n\n"
        f"ALSO, provide a concise, highly effective nutrition and recovery tip specially tailored "
        f"for this fitness goal.\n\n"
        f"Return the result as a JSON object with strictly two keys:\n"
        f"1. 'workout_plan': The workout plan in beautiful Markdown format.\n"
        f"2. 'nutrition_tip': The nutrition tip in beautiful Markdown format."
    )
    try:
        response = generate_with_retry(
            model,
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)
    except Exception as e:
        if is_rate_limit_error(e):
            return {
                "workout_plan": _fallback_plan(goal, intensity),
                "nutrition_tip": (
                    "Fallback tip: prioritize protein at each meal and maintain hydration; "
                    "retry in 1-2 minutes for an AI-personalized tip."
                ),
            }

        if is_model_not_found_error(e):
            return {
                "workout_plan": _fallback_plan(goal, intensity),
                "nutrition_tip": (
                    "Fallback tip: model configuration issue was detected and handled. "
                    "You still received a backup plan."
                ),
            }

        return {
            "workout_plan": f"Error generating plan: {str(e)}",
            "nutrition_tip": "Error generating tip."
        }
