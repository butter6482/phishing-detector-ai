# Phishing Detector

Detecta intentos de phishing en texto. Calcula un puntaje de riesgo (0–100), nivel de riesgo (safe / warning / phishing), palabras clave sospechosas, reputación de URLs (Google Safe Browsing) y una explicación generada por LLM (OpenRouter, opcional).

## Backend (FastAPI)

Rutas expuestas:
- GET `/` → `{ "ok": true }`
- GET `/health` → `{ "status": "ok" }`
- POST `/analyze` → body `{ "message": string, "lang": "es"|"en" }`

Respuesta:

```
{
  "nb": {"engine":"nb","label":"phishing|legit","phishing_score":0.42,"is_phishing":false,"confidence":"low","keywords":[]},
  "llm": {"verdict":"phishing","explanation":"...","advice":"..."} | null,
  "safebrowsing": {"urls": [...], "matches": [...], "has_threats": false},
  "final": {"score": 78, "risk":"phishing", "is_phishing": true, "label":"phishing", "explanation":"...", "source":"openrouter:phishing"}
}
```

### Ejecutar localmente

```
cd Backend
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api:app --host 127.0.0.1 --port 8000
```

Docs: http://127.0.0.1:8000/docs

## Frontend (Vite)

```
cd frontend
npm install
npm run dev
# http://127.0.0.1:5173
```

Configura `VITE_API_URL` en `.env` del frontend si necesitas apuntar a otra URL del backend.

## Variables de entorno

Coloca estas variables en `.env` (en la raíz o en `Backend/`):

```
OPENROUTER_API_KEY=sk-or-xxxx
OPENROUTER_MODEL=openai/gpt-3.5-turbo
USE_OPENROUTER=true
DECISION_UNCERTAIN_AS_PHISH=true
GOOGLE_SAFE_BROWSING_KEY=AIzaSy...
VITE_API_URL=http://127.0.0.1:8000
```

## Docker Compose (más adelante)

Se proveen `docker-compose.yml` y `docker-compose.dev.yml`. Una vez finalizada la configuración, ejecuta:

```
docker compose -f docker-compose.dev.yml up --build
```

## Tests

Incluye pruebas para extracción de URLs y llamada a Safe Browsing (con HTTP mock):

```
python -m pytest -q
```

