import streamlit as st
import os
import joblib
import requests
from openai import OpenAI
from dotenv import load_dotenv
from textos import textos

# Selección de idioma
idioma = st.selectbox("🌐 Selecciona idioma / Select language", ["Español", "English"])
t = textos[idioma]

# Cargar variables de entorno
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cargar modelo local y vectorizador
model = joblib.load("modelo_entrenado.pkl")
vectorizer = joblib.load("vectorizer.pkl")

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

# Función para verificar URLs con Google Safe Browsing
def verificar_urls_con_google(texto):
    api_key = os.getenv("GOOGLE_SAFE_BROWSING_KEY")
    url_api = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    urls_encontradas = [word for word in texto.split() if word.startswith("http")]
    urls_maliciosas = []

    for url in urls_encontradas:
        body = {
            "client": {"clientId": "phishing-detector", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        response = requests.post(url_api, json=body)
        if response.json().get("matches"):
            urls_maliciosas.append(url)

    return urls_maliciosas

# Interfaz Streamlit
st.title(t["titulo"])
st.write(t["instruccion"])

# INPUT DEL USUARIO
user_input = st.text_area(t["mensaje"])

# Solo se ejecuta si se aprieta el botón
if st.button(t["boton"]):
    if user_input.strip() == "":
        st.warning(t["advertencia_vacio"])
    else:
        # 1. Clasificación con modelo local
        input_vector = vectorizer.transform([user_input])
        prediction = model.predict(input_vector)[0]
        proba = model.predict_proba(input_vector)[0]
        st.write(f'{t["confianza"]} {max(proba) * 100:.2f}%')

        # 2. Palabras clave encontradas
        encontradas = [p for p in palabras_clave[idioma] if p.lower() in user_input.lower()]
        st.markdown(t["palabras_clave"])
        st.info(", ".join(encontradas) if encontradas else t["no_claves"])

        # 3. Preparar prompts para OpenAI
        if idioma == "Español":
            prompt = f"""Analiza el siguiente mensaje cuidadosamente. ¿Es un mensaje de phishing o es legítimo? Justifica tu análisis sin asumir que es falso solo por precaución. Considera el lenguaje, los enlaces, el tono, el remitente y el contenido del mensaje:\n\n{user_input}"""
            system_prompt = """Eres un experto en análisis de correos electrónicos. Tu tarea es determinar si un mensaje es phishing o legítimo, basándote en pruebas concretas. Sé neutral y no marques como phishing a menos que haya señales claras. Si no estás seguro, indícalo y sugiere cómo verificar el mensaje de forma segura."""
        else:
            prompt = f"""Carefully analyze the following message. Is it a phishing message or is it legitimate? Justify your analysis without assuming it's fake just out of caution. Consider the language, links, tone, sender, and content of the message:\n\n{user_input}"""
            system_prompt = """You are an expert in email analysis. Your task is to determine whether a message is phishing or legitimate based on concrete evidence. Be neutral and do not label something as phishing unless there are clear signs. If you're unsure, state that and suggest how to safely verify the message."""

        # 4. Explicación extendida con OpenAI
        try:
            st.markdown(t["explicacion_ia"])
            with st.spinner("Consultando IA..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                explanation = response.choices[0].message.content

                # Mostrar mensaje final basado en la explicación de IA
                explanation_lower = explanation.lower()
                if any(frase in explanation_lower for frase in [
                    # Español
                    "es un intento de phishing",
                    "hay múltiples señales claras de phishing",
                    "hay varias señales de alerta",
                    "este mensaje es sospechoso",
                    "no es seguro hacer clic",
                    # Inglés
                    "it is a phishing attempt",
                    "phishing attempt",
                    "strongly suggest it is phishing",
                    "highly likely that this message is a phishing attempt",
                    "this message is suspicious",
                    "this is suspicious",
                    "not safe to click"
                ]):
                    st.error("🚨 El mensaje parece ser phishing o spam.")
                elif any(frase in explanation_lower for frase in [
                    # Español
                    "no se puede confirmar que sea phishing",
                    "podría ser legítimo",
                    "se recomienda precaución",
                    # Inglés
                    "cannot be definitively confirmed",
                    "may be legitimate",
                    "exercise caution",
                    "could be legitimate",
                    "might be legitimate"
                ]):
                    st.warning("⚠️ El mensaje presenta señales sospechosas, pero no se puede confirmar que sea phishing.")
                else:
                    st.success("✅ El mensaje parece legítimo.")

                st.success(t["explicacion_generada"])
                st.info(explanation)

        except Exception as e:
            st.warning(t["error_openai"])
            st.text(str(e))

        # 5. Verificación de URLs maliciosas
        maliciosas = verificar_urls_con_google(user_input)
        st.markdown(t["verificacion_urls"])
        if maliciosas:
            st.error(f'{t["urls_maliciosas"]}\n\n{", ".join(maliciosas)}')
        else:
            st.info(t["urls_seguras"])
