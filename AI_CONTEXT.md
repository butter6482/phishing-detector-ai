# TuBot – AI Context

## Proyecto
- Frontend: React + Vite + Tailwind (carpeta: `frontend/`)
- Backend: FastAPI (Uvicorn) planificado (`Backend/`; los Dockerfiles ejecutan `uvicorn api:app`). Estado actual: `Backend/api.py` contiene utilidades de veredicto pero no define `app` ni rutas. Prototipo funcional con Flask en `prueba/api.py`.
- Auth/DB: TODO: no hay integración de Supabase ni persistencia en este repo.
- LLM: OpenRouter (integración en `Backend/src/openrouter.py` y en `prueba/api.py`).
- Docker: docker-compose con dos servicios (backend y frontend). Frontend se sirve con Nginx; backend con Uvicorn.
- Demo: TODO: no hay URL pública en `README.md`.

## Endpoints backend
Implementados en el prototipo Flask (`prueba/api.py`):

- `GET /` → `{"ok": true, "message": "...", "provider": "openrouter|openai"}`
- `GET /health` → `{"model_pkl": bool, "vectorizer_pkl": bool}`
- `POST /predict` → body `{"message": string}` → `{"engine":"nb","label":"phishing|legit","phishing_score":float,"is_phishing":bool}`
- `POST /analyze` → body `{"message": string, "lang": "es|en"}` → mezcla NB+LLM:
  - `{"nb": {...}, "llm": {...?}, "final": {...}}`

Planificado en `Backend/` (FastAPI):

- `POST /analyze` usando `Backend/src/schemas.py` (`AnalyzeRequest`/`AnalyzeResponse`) y `Backend/src/inference.py` + `Backend/src/openrouter.py`.
- TODO: definir `app` y registrar rutas en `Backend/api.py`.

Ejemplos:

```
# Análisis (prototipo Flask en 5000)
curl -s -X POST http://127.0.0.1:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"message":"Tu cuenta será suspendida, verifica aquí", "lang":"es"}'
```

## Variables de entorno

- Requeridas:
  - `OPENROUTER_API_KEY` (para habilitar llamadas al LLM)

- Opcionales y observadas en el repo:
  - `OPENROUTER_MODEL` (por defecto `"openai/gpt-3.5-turbo"` en `Backend/src/openrouter.py`)
  - `DECISION_UNCERTAIN_AS_PHISH` (`true|false`; por defecto `true` en `Backend/api.py`)
  - `USE_OPENROUTER` (prototipo `prueba/api.py`)
  - `OPENAI_API_KEY` (alternativa si no se usa OpenRouter; prototipo `prueba/api.py`)
  - `VITE_API_URL` (config del frontend)
  - `APP_URL`, `APP_NAME` (UI legacy Streamlit)
  - `GOOGLE_SAFE_BROWSING_KEY` (presente en `.env`, no se usa en el código actual)
  - Variables de test: `UNIT_TESTS`, `RUN_STREAMLIT_UI`

Ejemplo `.env` (sin valores):

```
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-3.5-turbo
DECISION_UNCERTAIN_AS_PHISH=true
VITE_API_URL=http://localhost:8000

# Opcionales / prototipo
USE_OPENROUTER=true
OPENAI_API_KEY=
APP_URL=
APP_NAME=
GOOGLE_SAFE_BROWSING_KEY=
```

## Dev local

- Compose (desarrollo):

```
docker compose -f docker-compose.dev.yml up --build
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

- Frontend sin Docker:

```
cd frontend
npm install
npm run dev
# http://localhost:5173
```

- Backend FastAPI sin Docker:
  - TODO: exponer `app` y rutas en `Backend/api.py` para ejecutar:
  - `uvicorn api:app --reload --host 127.0.0.1 --port 8000` (desde `Backend/`)

- Prototipo Flask:

```
python prueba/api.py
# API en http://127.0.0.1:5000
```

Nota frontend: `frontend/src/lib/api.ts` usa base fija `http://127.0.0.1:8000` actualmente.
- TODO: volver a usar `VITE_API_URL` o rutas relativas para despliegues.

## Docker (todo en uno)

- Estado actual: multi-servicio vía Compose (frontend y backend separados).

```
docker compose up --build
# Frontend: http://localhost:8080 (Nginx)
# Backend:  http://localhost:8000 (Uvicorn)
```

- TODO: si se requiere “todo en uno” en una sola imagen, faltaría integrar Nginx (estático) + reverse proxy a Uvicorn en la misma imagen.

## Deploy (Render, Web Service Docker)

- Estado: pensado para dos servicios (frontend 8080, backend 8000).
- Health check API: `GET /health` en el backend.
- Envs mínimos: `OPENROUTER_API_KEY` (y `OPENROUTER_MODEL` opcional).
- TODO: si Render exige un solo contenedor, consolidar imagen y configurar health en `/health` o ruta equivalente.

## Reglas para IA ayudante

- No cambiar estética ni rutas existentes sin pedirlo.
- Usar las rutas actuales: `POST /analyze` en el backend; preferir `VITE_API_URL` en el frontend para configurar el host.
- No introducir endpoints de persistencia (no hay `/api/bot` en este repo).
- Antes de refactorizar, proponer un diff pequeño y testeable (p.ej., exponer `app` en `Backend/api.py` y añadir `POST /analyze` con `schemas`).

