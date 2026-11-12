"""Configuration: API key and model name from the .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-3.5-flash-lite"


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def get_api_key() -> str:
    """Return the key without ever printing it."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing: check the .env file")
    return key