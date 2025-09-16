import re
from typing import Optional

COMMON_BRANDS = [
    "FirstBank", "First Bank", "Banco Popular", "Popular", "Microsoft", "Apple",
    "PayPal", "Amazon", "Google", "Meta", "Facebook", "Instagram", "Netflix",
    "Stripe", "GitHub", "Supabase", "Vercel",
]


def extract_org(text: str) -> Optional[str]:
    t = text.lower()
    for b in COMMON_BRANDS:
        if b.lower() in t:
            return b
    m = re.search(r"\b([a-z0-9-]+\.[a-z]{2,})(?:/[^\s]*)?", t)
    if m:
        base = m.group(1).split(".")[0]
        return base.capitalize()
    return None
