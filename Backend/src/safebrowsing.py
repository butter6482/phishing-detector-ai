import os
import re
from typing import List, Dict, Any

import httpx

GSB_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "").strip()

URL_RE = re.compile(
    r"((?:https?://)?(?:[\w-]+\.)+[a-zA-Z]{2,}(?:[/?#][^\s\"'<>]*)?)",
    re.IGNORECASE,
)


def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    found = [m.group(1) for m in URL_RE.finditer(text)]
    norm = [u if u.startswith(("http://", "https://")) else "http://" + u for u in found]
    seen, out = set(), []
    for u in norm:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def check_urls(text: str) -> Dict[str, Any]:
    urls = extract_urls(text)
    if not urls or not GSB_KEY:
        return {"urls": urls, "matches": [], "has_threats": False}

    body = {
        "client": {"clientId": "tubot-detector", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": u} for u in urls],
        },
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GSB_KEY}",
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return {"urls": urls, "matches": [], "has_threats": False}

    matches = data.get("matches", [])
    return {"urls": urls, "matches": matches, "has_threats": bool(matches)}

