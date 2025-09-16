import streamlit as st
import os
import re
import json
import joblib
import requests
from dotenv import load_dotenv
from textos import textos  # asumimos que ya lo tienes

# ========================
# Configuración / helpers
# ========================
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
GOOGLE_SAFE_BROWSING_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "").strip()
OPENROUTER_URL = "https://api.openrouter.ai/v1/chat/completions"
LLM_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct").strip()

# Umbrales
LOW_CONF = 0.4
HIGH_CONF = 0.6
STRONG_LOW = 0.2
STRONG_HIGH = 0.8

# Palabras clave sospechosas
palabras_clave = {
    "Español": [
        "verifica", "urgente", "cuenta suspendida", "haz clic", "contraseña",
        "seguro social", "actualiza", "información bancaria", "inicia sesión", "confirmar"
    ],
    "English": [
        "verify", "urgent", "account suspended", "click here", "password",
        "social security", "update", "bank information", "log in", "confirm"
    ]
}

# Cargar modelo local y vectorizador (NB)
@st.cache_resource
def _load_assets():
    model = joblib.load("modelo_entrenado.pkl")
    vectorizer = joblib.load("vectorizer.pkl")
    return model, vectorizer

model, vectorizer = _load_assets()

def nb_predict(texto: str):
    X = vectorizer.transform([texto])
    proba = model.predict_proba(X)[0]
    try:
        idx_phish = list(getattr(model, "classes_", [0,1])).index(1)
    except ValueError:
        import numpy as np
        idx_phish = int(proba.argmax())
    phish_score = float(proba[idx_phish])
    label = "phishing" if phish_score >= 0.5 else "legit"
    return phish_score, label

def find_urls(texto: str):
    url_pattern = re.compile(r"(https?://[^\s)>\]]+)", re.IGNORECASE)
    return url_pattern.findall(texto)

def verificar_urls_con_google(texto: str):
    if not GOOGLE_SAFE_BROWSING_KEY:
        return [], "⚠️ Falta GOOGLE_SAFE_BROWSING_KEY en .env (opcional)."
    urls = find_urls(texto)
    if not urls:
        return [], None

    url_api = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_KEY}"
    body = {
        "client": {"clientId": "phishing-detector", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": u} for u in urls]
        }
    }
    try:
        r = requests.post(url_api, json=body, timeout=12)
        r.raise_for_status()
        matches = r.json().get("matches", []) or []
        malos = sorted({m["threat"]["url"] for m in matches})
        return malos, None
    except Exception as e:
        return [], f"Error verificando URLs: {e}"

def llm_disponible() -> bool:
    return bool(OPENROUTER_API_KEY and LLM_MODEL)

# ======== IA: explicación corta en 1 frase ========
def llm_short_reason(texto: str, idioma: str) -> str:
    if not llm_disponible():
        return ""

    if idioma == "Español":
        system_prompt = (
            "Eres analista de seguridad. Devuelve SOLO una frase corta (máx 180 caracteres) "
            "que explique por qué el texto es phishing, legítimo o incierto. "
            "Empieza EXACTAMENTE con una de: 'phishing: ', 'legit: ' o 'uncertain: '."
        )
        user_prompt = f"Texto a evaluar:\n```\n{texto}\n```"
    else:
        system_prompt = (
            "You are a security analyst. Return ONLY one short sentence (max 180 chars) "
            "explaining why the text is phishing, legit, or uncertain. "
            "Start EXACTLY with one of: 'phishing: ', 'legit: ', or 'uncertain: '."
        )
        user_prompt = f"Text to evaluate:\n```\n{texto}\n```"

    body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8501"),
        "X-Title": os.getenv("APP_NAME", "PhishingDetectorStreamlit"),
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=30)
        r.raise_for_status()
        content = (r.json()["choices"][0]["message"]["content"] or "").strip()
        line = content.splitlines()[0].strip()
        return line[:200]
    except Exception:
        return ""

# ======== IA: análisis estructurado (JSON) ========
def llm_analyze(texto: str, idioma: str):
    if not llm_disponible():
        raise RuntimeError("IA desactivada: faltan OPENROUTER_API_KEY u OPENROUTER_MODEL.")

    if idioma == "Español":
        system_prompt = (
            "Eres un analista de seguridad. Devuelve SOLO un JSON válido con claves: "
            "label ('phishing'|'legit'|'uncertain'), score (0..1), reasons (lista de texto), "
            "explanation (breve en ESPAÑOL). No agregues texto fuera del JSON."
        )
        user_prompt = f"Analiza este texto y decide si es phishing o legítimo:\n```\n{texto}\n```"
    else:
        system_prompt = (
            "You are a security analyst. Return ONLY valid JSON with keys: "
            "label ('phishing'|'legit'|'uncertain'), score (0..1), reasons (string list), "
            "explanation (short in ENGLISH). Do not add any text outside the JSON."
        )
        user_prompt = f"Analyze this text and decide phishing vs legit:\n```\n{texto}\n```"

    body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8501"),
        "X-Title": os.getenv("APP_NAME", "PhishingDetectorStreamlit"),
    }

    r = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=40)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise
        data = json.loads(match.group(0))

    data["label"] = data.get("label", "uncertain")
    try:
        s = float(data.get("score", 0.5))
    except Exception:
        s = 0.5
    data["score"] = max(0.0, min(1.0, s))
    if not isinstance(data.get("reasons"), list):
        data["reasons"] = []
    data["explanation"] = data.get("explanation", "")
    return data

def fusion(nb_score: float, nb_label: str, llm_res: dict | None):
    decision = {
        "engine": "nb",
        "label": nb_label,
        "score": nb_score,
        "explanation": None,
        "reasons": []
    }
    # Si NB es muy seguro, nos quedamos con NB
    if nb_score <= STRONG_LOW or nb_score >= STRONG_HIGH:
        return decision

    # Si tenemos IA y NB está en zona no determinante, usamos/mezclamos
    if llm_res:
        llm_label = llm_res.get("label", nb_label)
        llm_score = float(llm_res.get("score", nb_score))

        # Casos de alta seguridad por cualquiera de los dos
        if nb_label == "phishing" and nb_score >= 0.8:
            return {
                "engine": "nb_strong",
                "label": "phishing",
                "score": nb_score,
                "explanation": llm_res.get("explanation"),
                "reasons": llm_res.get("reasons", [])
            }
        if llm_label == "phishing" and llm_score >= 0.8:
            return {
                "engine": "llm_strong",
                "label": "phishing",
                "score": llm_score,
                "explanation": llm_res.get("explanation"),
                "reasons": llm_res.get("reasons", [])
            }

        # Si coinciden etiquetas, promediamos
        if nb_label == llm_label:
            return {
                "engine": "hybrid_agree",
                "label": nb_label,
                "score": (nb_score + llm_score) / 2.0,
                "explanation": llm_res.get("explanation"),
                "reasons": llm_res.get("reasons", [])
            }

        # Si discrepan fuerte, marcamos como sospechoso
        if abs(llm_score - nb_score) >= 0.25:
            return {
                "engine": "hybrid_disagree",
                "label": "suspicious",
                "score": max(nb_score, llm_score),
                "explanation": llm_res.get("explanation"),
                "reasons": llm_res.get("reasons", [])
            }

        # Si no hay discrepancia fuerte, preferimos el más alto
        if llm_score >= nb_score:
            return {
                "engine": "llm_edge",
                "label": llm_label,
                "score": llm_score,
                "explanation": llm_res.get("explanation"),
                "reasons": llm_res.get("reasons", [])
            }
        else:
            return {
                "engine": "nb_edge",
                "label": nb_label,
                "score": nb_score,
                "explanation": llm_res.get("explanation"),
                "reasons": llm_res.get("reasons", [])
            }

    # Sin IA disponible o con error, devolvemos NB
    return decision

# ========================
#         UI
# ========================
if os.getenv("RUN_STREAMLIT_UI", "1") == "1":
    idioma = st.selectbox("🌐 Selecciona idioma / Select language", ["Español", "English"])
    t = textos[idioma]

    st.title(t["titulo"])
    st.write(t["instruccion"])
    user_input = st.text_area(t["mensaje"])

    # Opcional: permitir forzar IA y pedir explicación corta
    forzar_ia = st.checkbox("Forzar IA aunque NB esté seguro", value=False,
                            help="Útil si hay links o palabras sospechosas.")
    pedir_exp_corta = st.checkbox("Pedir explicación corta (IA)", value=True)

    if st.button(t["boton"]):
        if user_input.strip() == "":
            st.warning(t["advertencia_vacio"])
        else:
            # 1) NB
            nb_score, nb_label = nb_predict(user_input)
            st.write(f'{t["confianza"]} {nb_score * 100:.2f}% (NB)')

            # 2) Palabras clave + URLs
            encontradas = [p for p in palabras_clave[idioma] if p.lower() in user_input.lower()]
            st.markdown(t["palabras_clave"])
            st.info(", ".join(encontradas) if encontradas else t["no_claves"])
            urls_detectadas = find_urls(user_input)

            # 3) ¿Cuándo invocar IA?
            disparar_ia = (
                (LOW_CONF <= nb_score <= HIGH_CONF) or
                forzar_ia or
                (len(encontradas) >= 2) or
                (len(urls_detectadas) >= 1)
            )

            llm_res = None
            if disparar_ia and llm_disponible():
                try:
                    st.markdown(t.get("explicacion_ia", "🧠 Consultando IA para aclarar el caso…"))
                    with st.spinner("Consultando IA (OpenRouter)…"):
                        llm_res = llm_analyze(user_input, idioma)
                except Exception as e:
                    st.warning(t.get("error_openai", "⚠️ No se pudo obtener la explicación de IA."))
                    st.text(str(e))

            # 4) Fusión
            decision = fusion(nb_score, nb_label, llm_res)

            # 5) Mostrar resultado
            final_label = decision["label"]
            if final_label == "phishing":
                st.error("🚨 El mensaje parece **phishing**.")
            elif final_label in ("suspicious", "uncertain"):
                st.warning("⚠️ El mensaje es **sospechoso**; procede con precaución.")
            else:
                st.success("✅ El mensaje parece **legítimo**.")

            if decision.get("explanation"):
                st.success(t.get("explicacion_generada", "🧠 Explicación de la IA:"))
                st.info(decision["explanation"])
            if decision.get("reasons"):
                st.markdown("**Razones / Reasons:**")
                for r in decision["reasons"]:
                    st.write(f"- {r}")

            # 6) Explicación corta independiente
            if pedir_exp_corta and llm_disponible():
                with st.spinner("Pidiendo explicación corta a la IA…"):
                    breve = llm_short_reason(user_input, idioma)
                if breve:
                    lower = breve.lower()
                    if lower.startswith("phishing:"):
                        st.error(f"🧠 {breve}")
                    elif lower.startswith("legit:"):
                        st.success(f"🧠 {breve}")
                    else:
                        st.info(f"🧠 {breve}")
                else:
                    st.info("⚠️ No se pudo obtener la explicación corta de la IA.")

            # 7) Verificación de URLs (opcional)
            st.markdown(t["verificacion_urls"])
            urls_maliciosas, url_err = verificar_urls_con_google(user_input)
            if url_err:
                st.warning(url_err)
            elif urls_maliciosas:
                st.error(f'{t["urls_maliciosas"]}\n\n' + "\n".join(urls_maliciosas))
            else:
                st.info(t["urls_seguras"])
