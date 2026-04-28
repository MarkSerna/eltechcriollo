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
FROM nginx:stable-alpine

# Copiar el build compilado desde el Stage 1
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto estándar de servidor web
EXPOSE 80

# Comando para inyectar el DNS del sistema y arrancar Nginx
CMD ["/bin/sh", "-c", "export BACKEND_VAL=${VITE_API_URL:-techcriollo-api} && export BACKEND_CLEAN=${BACKEND_VAL#http://} && export BACKEND_CLEAN=${BACKEND_CLEAN#https://} && sed -i \"s|BACKEND_URL|$BACKEND_CLEAN:8000|g\" /etc/nginx/conf.d/default.conf && echo \"Waiting for backend $BACKEND_CLEAN:8000...\" && while ! nc -z $BACKEND_CLEAN 8000; do sleep 2; done && echo \"Backend up! Starting Nginx.\" && nginx -g 'daemon off;'"]
