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

CMD ["nginx", "-g", "daemon off;"]
