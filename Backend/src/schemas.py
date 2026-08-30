from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


Lang = Literal["es", "en"]


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=20000)
    lang: Lang = Field("es")


class NBResult(BaseModel):
    engine: str
    label: Literal["phishing", "legit"]
    phishing_score: float
    is_phishing: bool
    confidence: Literal["low", "medium", "high"]
    keywords: list[str] = []


class LLMResult(BaseModel):
    verdict: Literal["phishing", "safe", "uncertain"]
    explanation: str
    advice: Optional[str] = None


class SafeBrowsingResult(BaseModel):
    urls: list[str]
    matches: list[dict[str, Any]]
    has_threats: bool


class FinalResult(BaseModel):
    engine: str = "fused"
    score: int
    risk: Literal["safe", "warning", "phishing"]
    is_phishing: bool
    label: Literal["phishing", "legit"]
    explanation: str
    source: str
    llm_error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    nb: NBResult
    llm: Optional[LLMResult] = None
    safebrowsing: SafeBrowsingResult
    final: FinalResult
