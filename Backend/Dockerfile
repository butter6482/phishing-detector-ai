# ---------- build runtime ----------
FROM python:3.12-slim

# faster, smaller builds
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# system deps (uvicorn performance)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# requirements first for layer caching
COPY Backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# copy app
COPY Backend /app

# non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
