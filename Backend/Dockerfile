FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 
    PYTHONUNBUFFERED=1 
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

# requirements (siempre desde la ra?z usando la ruta Backend/)
COPY Backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# c?digo del backend
COPY Backend/ /app/

# usuario no-root (opcional)
RUN useradd -m appuser || true
USER appuser

EXPOSE 8000

# Arranque seguro: python -m uvicorn para evitar issues de PATH
CMD ["python","-m","uvicorn","api:app","--host","0.0.0.0","--port","8000"]
# Backend/Dockerfile
# Construye desde la RAÍZ del repo y copia código/requirements desde Backend/
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Paquetes de sistema (compilación ruedas nativas + utilidades)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Requirements (siempre referenciando la carpeta Backend/)
COPY Backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# Código del backend (FastAPI)
COPY Backend/ /app/

# Usuario no root (opcional)
RUN useradd -m appuser || true
USER appuser

EXPOSE 8000

# Arranque: usar python -m para evitar issues de PATH
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
