from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import os, json, re

import joblib
import requests

# ── IA providers (elige por ENV) ────────────────────────────────────────────────
# OpenAI SDK v1
try:
    from openai import OpenAI  # pip install openai==1.9.0 o mayor
except Exception:
    OpenAI = None

load_dotenv()

USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
OPENROUTER_URL = "https://api.openrouter.ai/v1/chat/completions"

# ── Umbrales del NB ────────────────────────────────────────────────────────────
LOW_CONF = 0.4
HIGH_CONF = 0.6
STRONG_LOW = 0.2
STRONG_HIGH = 0.8

# ── Flask ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ── Carga de artefactos (con mensajes claros) ─────────────────────────────────
ART_MODEL = Path("modelo_entrenado.pkl")
ART_VEC = Path("vectorizer.pkl")

def load_artifacts():
    missing = []
    if not ART_MODEL.exists(): missing.append(str(ART_MODEL))
    if not ART_VEC.exists(): missing.append(str(ART_VEC))
    if missing:
        raise FileNotFoundError(
            "Faltan artefactos del modelo. Entrena con train_nb.py o coloca los .pkl aquí: "
            + ", ".join(missing)
        )
    model = joblib.load(ART_MODEL)
    vectorizer = joblib.load(ART_VEC)
    return model, vectorizer

model, vectorizer = load_artifacts()

# ── Utilidades ─────────────────────────────────────────────────────────────────
def nb_predict(text: str):
    X = vectorizer.transform([text])
    proba = model.predict_proba(X)[0]
    idx_phish = list(model.classes_).index(1)  # clase 1 = spam/phishing
    phish_score = float(proba[idx_phish])
    label = "phishing" if phish_score >= 0.5 else "legit"
    return phish_score, label

def llm_analyze(text: str, lang: str = "es"):
    """
    Usa OpenRouter si USE_OPENROUTER=true, de lo contrario OpenAI.
    Devuelve dict con: label, score, reasons, explanation
    """
    sys_es = ("Eres analista de seguridad. Devuelve SOLO JSON válido con claves: "
              "label('phishing'|'legit'|'uncertain'), score(0..1), reasons(lista), explanation(texto corto en ESPAÑOL).")
    sys_en = ("You are a security analyst. Return ONLY valid JSON with keys: "
              "label('phishing'|'legit'|'uncertain'), score(0..1), reasons(list), explanation(short ENGLISH text).")
    system_prompt = sys_es if lang == "es" else sys_en
    user_prompt = f"Analiza y clasifica este texto:\n```\n{text}\n```" if lang == "es" else f"Analyze and classify this text:\n```\n{text}\n```"

    if USE_OPENROUTER:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("Falta OPENROUTER_API_KEY en .env")
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        r = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=30)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
    else:
        if not OPENAI_API_KEY:
            raise RuntimeError("Falta OPENAI_API_KEY en .env")
        if OpenAI is None:
            raise RuntimeError("openai SDK no disponible. Instala: pip install openai")
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content.strip()

    # Parseo robusto de JSON (por si el modelo habla de más)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m:
            raise
        return json.loads(m.group(0))

def fuse(nb_score: float, nb_label: str, llm_res: dict | None):
    decision = {
        "engine": "nb",
        "label": nb_label,
        "score": nb_score,
        "explanation": None,
        "reasons": []
    }
    if nb_score <= STRONG_LOW or nb_score >= STRONG_HIGH:
        return decision

    if LOW_CONF <= nb_score <= HIGH_CONF and llm_res:
        decision.update({
            "engine": "llm",
            "label": llm_res.get("label", nb_label),
            "score": llm_res.get("score", nb_score),
            "explanation": llm_res.get("explanation"),
            "reasons": llm_res.get("reasons", []),
        })
        return decision

    if llm_res:
        llm_label = llm_res.get("label", nb_label)
        llm_score = llm_res.get("score", nb_score)
        if (nb_label != llm_label) and (abs(llm_score - nb_score) >= 0.25):
            decision.update({
                "engine": "hybrid_disagree",
                "label": "suspicious",
                "score": max(nb_score, llm_score),
                "explanation": llm_res.get("explanation"),
                "reasons": llm_res.get("reasons", []),
            })
    return decision

# ── Rutas ──────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True, "message": "Phishing Detector API ✅", "provider": "openrouter" if USE_OPENROUTER else "openai"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"model_pkl": ART_MODEL.exists(), "vectorizer_pkl": ART_VEC.exists()})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    msg = data.get("message")
    if not msg:
        return jsonify({"error": "Falta 'message'"}), 400

    score, nb_label = nb_predict(msg)
    return jsonify({
        "engine": "nb",
        "label": nb_label,
        "phishing_score": round(score, 4),
        "is_phishing": (nb_label == "phishing")
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Flujo híbrido:
    - NB siempre.
    - Si NB ∈ [0.4, 0.6], llama LLM y fusiona.
    """
    data = request.get_json(silent=True) or {}
    msg = data.get("message")
    lang = data.get("lang", "es")  # 'es' o 'en'
    if not msg:
        return jsonify({"error": "Falta 'message'"}), 400

    nb_score, nb_label = nb_predict(msg)
    llm_res = None
    if LOW_CONF <= nb_score <= HIGH_CONF:
        try:
            llm_res = llm_analyze(msg, "es" if lang.lower().startswith("es") else "en")
        except Exception as e:
            # no caigas por un fallo del LLM
            llm_res = None

    decision = fuse(nb_score, nb_label, llm_res)
    return jsonify({
        "nb": {"score": round(nb_score, 4), "label": nb_label},
        "llm": llm_res,
        "final": decision
    })

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("✅ Iniciando la API de Flask en http://127.0.0.1:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)
