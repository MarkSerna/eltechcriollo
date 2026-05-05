# --- STAGE 1: Build React Frontend ---
FROM node:20-slim AS build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

# --- STAGE 2: Servir con Nginx ---
FROM nginx:stable-alpine

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Usar variable de entorno BACKEND_URL o valor por defecto
CMD ["/bin/sh", "-c", "
  BACKEND_URL=${BACKEND_URL:-https://techcriollo-api.onrender.com}
  # Extraer host y puerto de la URL
  BACKEND_HOST=$(echo $BACKEND_URL | sed 's|https://||' | sed 's|http://||' | cut -d':' -f1)
  BACKEND_PORT=$(echo $BACKEND_URL | grep ':' | cut -d':' -f3 || echo '443')
  if [ -z \"$BACKEND_PORT\" ] || [ \"$BACKEND_PORT\" = \"$BACKEND_HOST\" ]; then
    BACKEND_PORT=443
  fi
  echo \"Configurando proxy hacia: $BACKEND_HOST:$BACKEND_PORT\"
  # Actualizar nginx.conf
  sed -i \"s|set \\$backend \\\"techcriollo-api\\\"|set \\$backend \\\"$BACKEND_HOST\\\"|g\" /etc/nginx/conf.d/default.conf
  sed -i \"s|set \\$backend_port 8000|set \\$backend_port $BACKEND_PORT|g\" /etc/nginx/conf.d/default.conf
  nginx -g 'daemon off;'
"]