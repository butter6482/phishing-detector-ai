from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
from dotenv import load_dotenv
import openai  # Usamos el cliente clásico

# Inicializar Flask
app = Flask(__name__)
CORS(app)

# Cargar modelo y vectorizador
model = joblib.load("modelo_entrenado.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# Cargar clave de OpenAI
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ruta principal
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API funcionando correctamente."})

# Ruta de predicción
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Falta el campo 'message' en el cuerpo JSON"}), 400

    message = data["message"]
    vect_msg = vectorizer.transform([message])
    prediction = model.predict(vect_msg)[0]
    proba = model.predict_proba(vect_msg)[0]

    return jsonify({
        "is_phishing": bool(prediction),
        "confidence": round(float(max(proba)), 4)
    })

# Ruta de explicación con OpenAI
@app.route("/explain", methods=["POST"])
def explain():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Falta el campo 'message' en el cuerpo JSON"}), 400

    user_input = data["message"]
    prompt = f"""Analiza el siguiente mensaje cuidadosamente. ¿Es un mensaje de phishing o es legítimo? Justifica tu análisis sin asumir que es falso solo por precaución. Considera el lenguaje, los enlaces, el tono, el remitente y el contenido del mensaje:\n\n{user_input}"""

    system_prompt = """Eres un experto en análisis de correos electrónicos. Tu tarea es determinar si un mensaje es phishing o legítimo, basándote en pruebas concretas. Sé neutral y no marques como phishing a menos que haya señales claras. Si no estás seguro, indícalo y sugiere cómo verificar el mensaje de forma segura."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        explanation = response.choices[0].message["content"]
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ejecutar la app
if __name__ == "__main__":
    print("✅ Iniciando la API de Flask...")
    app.run(debug=True, port=5000)
