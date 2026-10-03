import time
import google.generativeai as genai


MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2


def is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    rate_limit_markers = (
        "429",
        "too many requests",
        "resource_exhausted",
        "quota",
        "rate limit",
    )
    return any(marker in message for marker in rate_limit_markers)


def is_model_not_found_error(exc: Exception) -> bool:
    message = str(exc).lower()
    model_error_markers = (
        "404",
        "not found for api version",
        "models/",
        "unsupported for generatecontent",
    )
    return any(marker in message for marker in model_error_markers)


def build_model(preferred_models: list[str]):
    fallback_order = [
        "gemini-3.8-flash",
        "gemini-flash-latest",
    ]

    candidates = preferred_models + fallback_order

    try:
        models = list(genai.list_models())
        supported = {
            m.name.replace("models/", "")
            for m in models
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        }

        for candidate in candidates:
            if candidate in supported:
                return genai.GenerativeModel(candidate)
    except Exception:
        # If discovery fails, fall back to the first candidate and let runtime handling manage errors.
        pass

    return genai.GenerativeModel(candidates[0])


def generate_with_retry(model, prompt: str, generation_config=None):
    for attempt in range(MAX_RETRIES):
        try:
            return model.generate_content(prompt, generation_config=generation_config)
        except Exception as exc:
            if not is_rate_limit_error(exc) or attempt == MAX_RETRIES - 1:
                raise

            # Exponential backoff helps absorb short bursts and avoid immediate rejections.
            wait_time = BASE_DELAY_SECONDS * (2 ** attempt)
            time.sleep(wait_time)
