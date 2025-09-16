import os
from typing import Optional, Tuple, Dict, Any, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from src.schemas import AnalyzeRequest, AnalyzeResponse
except Exception:  # pragma: no cover
    from pydantic import BaseModel

    class AnalyzeRequest(BaseModel):
        message: str
        lang: Literal["es", "en"] = "es"

    class AnalyzeResponse(BaseModel):  # simplified for docs if schemas import fails
        nb: dict
        llm: Optional[dict] = None
        safebrowsing: dict
        final: dict

try:
    from src.inference import run_analysis_pipeline
except Exception:  # pragma: no cover
    def run_analysis_pipeline(message: str, lang: str, llm: Dict[str, Any] | None):
        t = (message or "").lower()
        is_phish = any(x in t for x in ["verifica", "suspendida", "click aqui", "urgente", "bank", "password"])
        nb = {
            "engine": "nb",
            "label": "phishing" if is_phish else "legit",
            "phishing_score": 0.85 if is_phish else 0.05,
            "is_phishing": is_phish,
            "confidence": "high" if is_phish else "low",
            "keywords": [k for k in ["verifica", "suspendida", "click aqui", "urgente"] if k in t],
        }
        sb = {"urls": [], "matches": [], "has_threats": False}
        score = 80 if is_phish else 10
        risk = "phishing" if is_phish else "safe"
        final_bool = is_phish
        label = "phishing" if is_phish else "legit"
        return nb, sb, score, risk, final_bool, label

try:
    from src.openrouter import call_openrouter
except Exception:  # pragma: no cover
    def call_openrouter(*args, **kwargs):
        return None

try:
    from src.brand import extract_org
except Exception:  # pragma: no cover
    def extract_org(_: str) -> Optional[str]:
        return None


app = FastAPI(title="TuBot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}


def _get_text_and_lang(req: AnalyzeRequest) -> Tuple[str, str]:
    data = req.model_dump() if hasattr(req, "model_dump") else (req.dict() if hasattr(req, "dict") else dict(req))
    msg = data.get("message") or data.get("text") or data.get("prompt") or ""
    lang = data.get("lang") or data.get("language") or "es"
    return msg, lang


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    try:
        text, lang = _get_text_and_lang(req)
        llm = call_openrouter(text, lang)
        nb, sb, score, risk, final_bool, label = run_analysis_pipeline(text, lang, llm if isinstance(llm, dict) else None)

        if isinstance(llm, dict) and not llm.get("error"):
            explanation = llm.get("explanation", "")
            advice = llm.get("advice", "")
            if advice:
                explanation = (explanation + f"\n\nRecomendación: {advice}").strip()
            source = f"openrouter:{llm.get('verdict','uncertain')}"
            llm_out = {
                "verdict": llm.get("verdict", "uncertain"),
                "explanation": llm.get("explanation", ""),
                "advice": llm.get("advice", ""),
            }
        else:
            # If an LLM error occurred, surface it for debugging in the client
            has_error = isinstance(llm, dict) and bool(llm.get("error"))
            source = (
                "fallback:llm_error" if has_error else (
                    "fallback:no_llm_safe" if risk == "safe" else (
                        "fallback:no_llm_phish" if risk == "phishing" else "fallback:no_llm_warning"
                    )
                )
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

        # Attach LLM error only if there was an attempted call that failed
        if isinstance(llm, dict) and llm.get("error"):
            final["llm_error"] = str(llm.get("error"))

        return {
            "nb": nb,
            "llm": llm_out,
            "safebrowsing": {"urls": sb.get("urls", []), "matches": sb.get("matches", []), "has_threats": sb.get("has_threats", False)},
            "final": final,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
