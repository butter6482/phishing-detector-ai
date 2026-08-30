import logging
import os
import time
from collections import deque
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv es opcional en producción
    pass

from src.inference import run_analysis_pipeline
from src.openrouter import call_openrouter
from src.schemas import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger("phishing_detector")

app = FastAPI(title="Phishing Detector Backend")

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_allowed_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Rate limit sencillo en memoria (por IP, ventana deslizante) ---
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
_RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
_hits: dict[str, deque[float]] = {}
_hits_lock = Lock()


def _rate_limited(client_ip: str) -> bool:
    now = time.monotonic()
    with _hits_lock:
        bucket = _hits.setdefault(client_ip, deque())
        while bucket and now - bucket[0] > _RATE_WINDOW:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT:
            return True
        bucket.append(now)
        return False


@app.get("/")
async def root():
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if _rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests")

    text, lang = req.message, req.lang
    try:
        llm = call_openrouter(text, lang)
        llm_dict = llm if isinstance(llm, dict) else None
        nb, sb, score, risk, final_bool, label = run_analysis_pipeline(text, lang, llm_dict)
    except Exception:
        logger.exception("analyze pipeline failed")
        raise HTTPException(status_code=500, detail="Analysis failed")

    llm_ok = isinstance(llm, dict) and not llm.get("error")
    if llm_ok:
        explanation = llm.get("explanation", "")
        advice = llm.get("advice", "")
        if advice:
            explanation = f"{explanation}\n\nRecomendación: {advice}".strip()
        source = f"openrouter:{llm.get('verdict', 'uncertain')}"
        llm_out = {
            "verdict": llm.get("verdict", "uncertain"),
            "explanation": llm.get("explanation", ""),
            "advice": llm.get("advice", ""),
        }
    else:
        has_error = isinstance(llm, dict) and bool(llm.get("error"))
        source = (
            "fallback:llm_error"
            if has_error
            else f"fallback:no_llm_{risk if risk in ('safe', 'phishing') else 'warning'}"
        )
        explanation = "Automated assessment based on local heuristics and URL reputation."
        llm_out = None

    final = {
        "engine": "fused",
        "score": score,
        "risk": risk,
        "is_phishing": final_bool,
        "label": label,
        "explanation": explanation,
        "source": source,
    }
    if isinstance(llm, dict) and llm.get("error"):
        final["llm_error"] = str(llm.get("error"))

    return {
        "nb": nb,
        "llm": llm_out,
        "safebrowsing": {
            "urls": sb.get("urls", []),
            "matches": sb.get("matches", []),
            "has_threats": sb.get("has_threats", False),
        },
        "final": final,
    }
