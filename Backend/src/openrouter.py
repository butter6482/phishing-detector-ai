import json
import os
from typing import Any, Dict, Optional

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SYSTEM = (
    "You are a security analyst. Given an email/message, classify it as 'phishing' or 'safe'. "
    "Return strict JSON with fields: verdict ('phishing'|'safe'|'uncertain'), "
    "explanation (<=120 words, same language as the input), advice (short actionable guidance)."
)


def _config() -> tuple[str, str, bool]:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    enabled = os.getenv("USE_OPENROUTER", "true").lower() == "true"
    return key, model, enabled


def call_openrouter(message: str, lang: str = "es") -> Optional[Dict[str, Any]]:
    key, model, enabled = _config()
    if not enabled or not key:
        return None

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Language: {lang}\nMessage:\n{message[:4000]}"},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=15) as client:
            r = client.post(OPENROUTER_URL, headers=headers, json=body)
            if r.status_code == 429:
                return {"error": "openrouter_rate_limited"}
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        obj = json.loads(content)
        return {
            "verdict": str(obj.get("verdict", "uncertain")).lower(),
            "explanation": str(obj.get("explanation", "")).strip(),
            "advice": str(obj.get("advice", "")).strip(),
        }
    except Exception as e:
        return {"error": f"openrouter_error: {e}"}
