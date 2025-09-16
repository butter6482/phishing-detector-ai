import re
import unicodedata
from typing import Dict, Any

from joblib import load

_model = None
_vec = None


def load_model():
    global _model, _vec
    if _model is None or _vec is None:
        try:
            _model = load("backend/models/modelo_entrenado.pkl")
            _vec = load("backend/models/vectorizer.pkl")
        except Exception:
            _model = None
            _vec = None
    return _model, _vec


LEET_MAP = str.maketrans({
    "0": "o",
    "1": "l",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
})


def normalize(text: str) -> str:
    t = text.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.translate(LEET_MAP)
    return t


SEEDS = [
    r"\b(urgente|inmediato|ultimo\s+aviso|24\s*h|plazo\s*limite|expira\s*hoy)\b",
    r"\b(suspension|suspendida|bloquead[ao]|desactivad[ao]|cerrar(?:emos)?\s+tu\s+cuenta)\b",
    r"\b(actividad\s+inusual|acceso\s+no\s+autorizado|comprometid[ao])\b",
    r"\b(verifica(?:r)?|confirmar|validar|autentica(?:r)?|comprobar\s*identidad)\b",
    r"\b(restablece(?:r)?\s*(?:la\s*)?(?:contrasena|password|clave)|cambio\s+de\s+(?:password|contrasena))\b",
    r"\b(inicia(?:r)?\s+sesion|log[\s-]?in|sign[\s-]?in|sign[\s-]?on)\b",
    r"\b(codigo|otp|2fa|token|pin)\b",
    r"\b(haz|haga)\s+clic\s+(?:aqui|enlace|link)\b",
    r"\b(actualiza(?:r)?\s+(?:datos|informacion)|proporciona(?:r)?\s+(?:datos|informacion))\b",
    r"\b(numero\s+de\s+(?:tarjeta|seguridad|ssn)|tarjeta\s+de\s+credito|cvv|iban|swift)\b",
    r"\b(transferencia|wire|zelle|western\s+union|crypto|bitcoin|usdt|wallet)\b",
    r"\b(banco|cuenta|sucursal|cajero|tarjeta)\b",
    r"\b(factura|pago\s+pendiente|pago\s+fallido|overdue|outstanding)\b",
    r"\b(reembolso|refund|premio|ganador|loteria|sorteo|gift\s*card|voucher)\b",
    r"\b(envio|tracking|seguimiento|paquete\s+retenido|aduana|customs)\b",
    r"\b(dhl|fedex|ups|usps|royal\s*mail|correos)\b",
    r"https?://\d{1,3}(?:\.\d{1,3}){3}\b",
    r"https?://(?:[a-z0-9-]+\.)*xn--[a-z0-9-]+\b",
    r"https?://(?:bit\.ly|goo\.gl|t\.co|tinyurl\.com|ow\.ly|cutt\.ly|rb\.gy|is\.gd|s\.id)/\w+",
    r"\b(?<!@)[a-z0-9-]{2,}\.(?:top|xyz|link|live|shop|click|pw|ru|su|work|rest)\b",
    r"\b(adjunto|attachment|comprobante|invoice)\b",
    r"\.(?:html?|xlsm?|docm?|scr|exe|bat|js)\b",
    r"\b(departamento\s+de\s+seguridad|it\s+support|help\s*desk|verificacion\s+de\s+seguridad)\b",
    r"\b(verify|validate|confirm|update\s+account|reset\s+password)\b",
    r"\b(account\s+suspended|unusual\s+activity|unauthorized\s+access)\b",
]


PATTERNS = [re.compile(p, re.IGNORECASE) for p in SEEDS]


def keyword_hits(text: str):
    t = normalize(text)
    hits = []
    for pat in PATTERNS:
        if pat.search(t):
            label = pat.pattern
            if "bit\\.ly" in label or "tinyurl" in label:
                label = "url_shortener"
            elif "xn--" in label:
                label = "punycode_domain"
            elif "http" in label and "\\d{1,3}" in label:
                label = "ip_url"
            hits.append(label)
    seen, uniq = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq


def predict_proba(text: str) -> float:
    model, vec = load_model()
    if model and vec:
        X = vec.transform([text])
        return float(model.predict_proba(X)[0, 1])
    hits = len(keyword_hits(text))
    base = 0.08
    step = 0.10
    return min(base + step * hits, 0.98)


def analyze_local(text: str) -> Dict[str, Any]:
    p = predict_proba(text)
    is_phish = p >= 0.5
    words = keyword_hits(text)
    if p <= 0.3 or p >= 0.7:
        confidence = "high"
    elif 0.3 < p < 0.7:
        confidence = "medium"
    else:
        confidence = "low"
    return {
        "score": round(p, 3),
        "is_phishing": is_phish,
        "keywords": words,
        "confidence": confidence,
    }


def analyze_message(message: str, lang: str = "es") -> Dict[str, Any]:
    local = analyze_local(message)
    return {
        "engine": "nb",
        "label": "phishing" if local["is_phishing"] else "legit",
        "phishing_score": float(local["score"]),
        "is_phishing": bool(local["is_phishing"]),
        "confidence": str(local["confidence"]),
        "keywords": list(local.get("keywords", [])),
    }


def compute_score(local: Dict[str, Any], sb: Dict[str, Any], llm: Dict[str, Any] | None) -> int:
    base = int(max(0.0, min(1.0, float(local.get("phishing_score", 0.0)))) * 100)
    if sb.get("has_threats"):
        base = max(base, 70)
    if isinstance(llm, dict):
        v = str(llm.get("verdict", "uncertain")).lower()
        if v == "phishing":
            base = max(base, 80)
        elif v == "safe":
            base = min(base, 30)
    return max(0, min(100, base))


def risk_from_score(score: int) -> str:
    if score < 40:
        return "safe"
    if score < 60:
        return "warning"
    return "phishing"


def run_analysis_pipeline(message: str, lang: str, llm: Dict[str, Any] | None):
    from .safebrowsing import check_urls

    nb = analyze_message(message, lang)
    sb = check_urls(message)
    score = compute_score(nb, sb, llm)
    risk = risk_from_score(score)
    final_bool = risk == "phishing"
    label = "phishing" if final_bool else "legit"
    return nb, sb, score, risk, final_bool, label

