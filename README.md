# 🛡️ Phishing Detector — AI-powered email risk analyzer

<https://phishing-detector-ai.onrender.com>

Analiza correos sospechosos y devuelve un veredicto claro con puntuación de riesgo
(0–100), palabras clave detectadas y una explicación generada por IA. Combina tres
señales: un clasificador local (Naive Bayes con fallback heurístico), validación de
URLs con Google Safe Browsing y un LLM vía OpenRouter.

## Arquitectura

| Capa       | Tecnología                                        |
|------------|---------------------------------------------------|
| Frontend   | React + Vite + TailwindCSS + TypeScript           |
| Backend    | FastAPI (Uvicorn) — endpoint `POST /api/analyze`  |
| ML local   | scikit-learn (`Backend/models/*.pkl`)             |
| URLs       | Google Safe Browsing API                          |
| LLM        | OpenRouter                                        |
| Infra      | Imagen Docker única (nginx + uvicorn + supervisord)|

El flujo (`Backend/src/inference.py`): modelo local → Safe Browsing → LLM → score
fusionado (`compute_score`) → nivel de riesgo `safe` / `warning` / `phishing`.

## Desarrollo local

Backend:

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r Backend/requirements.txt
cp .env.example Backend/.env                         # completa las claves
cd Backend && uvicorn api:app --reload --port 8000
```

Frontend (usa el proxy de Vite hacia `127.0.0.1:8000`):

```bash
cd frontend
npm install
npm run dev
```

## Docker (producción)

```bash
docker compose up --build
# app en http://localhost:8080
```

## Variables de entorno

Ver `.env.example`. Claves:

| Variable                   | Descripción                                             |
|----------------------------|--------------------------------------------------------|
| `OPENROUTER_API_KEY`       | Clave de OpenRouter. Sin ella, el LLM se omite.        |
| `USE_OPENROUTER`           | `true`/`false` para activar el LLM.                    |
| `GOOGLE_SAFE_BROWSING_KEY` | Clave de Safe Browsing. Sin ella, se omite el chequeo. |
| `ALLOWED_ORIGINS`          | Orígenes CORS separados por coma.                      |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | Límite por IP en `/analyze`. |

## Tests

```bash
cd Backend && pytest -q
```

## Reentrenar el modelo

```bash
pip install -r Backend/scripts/requirements-train.txt
python Backend/scripts/train_nb.py   # escribe Backend/models/*.pkl
```
