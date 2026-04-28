# --- STAGE 1: Build React Frontend ---
FROM node:20-slim AS build-stage

WORKDIR /app

# Instalar dependencias
COPY package*.json ./
RUN npm install

# Copiar código y compilar para producción
COPY . .
RUN npm run build

# --- STAGE 2: Servir con Nginx ---
FROM nginx:stable

# Copiar el build compilado desde el Stage 1
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto estándar de servidor web
EXPOSE 80

# Comando para inyectar el host del backend y arrancar Nginx inmediatamente
CMD ["/bin/sh", "-c", "export BACKEND_VAL=${VITE_API_URL:-techcriollo-api} && export BACKEND_CLEAN=${BACKEND_VAL#http://} && export BACKEND_CLEAN=${BACKEND_CLEAN#https://} && sed -i \"s|BACKEND_URL|$BACKEND_CLEAN:8000|g\" /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
