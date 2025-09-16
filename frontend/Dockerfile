# ---------- build ----------
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
# asegúrate que tu build use rutas relativas o setea BASE_URL si lo necesitas
RUN npm run build

# ---------- serve ----------
FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY --from=build /app/dist ./

# nginx config mínimo
COPY --from=build /app/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
