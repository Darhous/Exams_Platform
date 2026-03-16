import os
import json
from typing import Any, Dict, Optional

from google import genai
from google.genai import types


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


GEMINI_API_KEY = _get_env("GEMINI_API_KEY") or _get_env("GOOGLE_API_KEY")
GEMINI_MODEL = _get_env("GEMINI_MODEL", "models/gemini-2.5-flash")
GEMINI_ENABLED = _get_env("GEMINI_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def is_gemini_ready() -> bool:
    return bool(GEMINI_ENABLED and GEMINI_API_KEY)


def _client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY")
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_json(
    prompt: str,
    schema: Dict[str, Any],
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    max_output_tokens: int = 4096,
) -> Dict[str, Any]:
    client = _client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_json_schema=schema,
        ),
    )
    text = (response.text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {"raw_text": text}
