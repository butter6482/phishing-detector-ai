import os, json, httpx
from typing import Optional, Dict, Any

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "true").lower() == "true"

HEADERS = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
SYSTEM = (
    "You are a security analyst. Given an email/message, classify it as 'phishing' or 'safe'. "
    "Return strict JSON with fields: verdict ('phishing'|'safe'|'uncertain'), "
    "explanation (<=120 words, same language as the input), advice (short actionable guidance)."
)


def call_openrouter(message: str, lang: str = "es") -> Optional[Dict[str, Any]]:
    if not USE_OPENROUTER or not OPENROUTER_API_KEY:
        return None
    prompt = f"Language: {lang}\nMessage:\n{message[:4000]}"
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }
    try:
        with httpx.Client(timeout=15) as client:
            r = client.post("https://openrouter.ai/api/v1/chat/completions", headers=HEADERS, json=body)
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
