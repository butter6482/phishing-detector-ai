# All-in-one: build frontend, install backend, run nginx + uvicorn via supervisord

#######################
# 1) Frontend build
#######################
FROM node:20-alpine AS frontend-build
WORKDIR /src-frontend
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend/ .
RUN npm run build

#######################
# 2) Final image
#######################
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System packages: nginx + supervisor + build tools for wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx supervisor build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Backend deps
COPY Backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# Backend code
COPY Backend/ /app/

# Frontend build -> nginx html
RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default
COPY --from=frontend-build /src-frontend/dist /usr/share/nginx/html

# Nginx + Supervisor configs
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Non-root user (optional)
RUN useradd -m appuser || true \
    && mkdir -p /var/cache/nginx /var/run/nginx \
    && chown -R appuser:appuser /var/lib/nginx /var/log/nginx /var/cache/nginx /var/run/nginx /var/run

EXPOSE 80

CMD ["/usr/bin/supervisord","-n","-c","/etc/supervisor/conf.d/supervisord.conf"]
