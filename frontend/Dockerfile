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
# Comando ultra-robusto: busca el backend en red interna y pública
CMD ["/bin/sh", "-c", "export B_HOST=${VITE_API_URL:-techcriollo-api} && export B_HOST=${B_HOST#http://} && export B_HOST=${B_HOST#https://} && export B_HOST=${B_HOST%/} && echo \"[INIT] Buscando backend en: $B_HOST, $B_HOST.render.internal y $B_HOST.onrender.com\" && (for i in $(seq 1 60); do for TARGET in \"$B_HOST\" \"$B_HOST.render.internal\" \"$B_HOST.onrender.com\"; do if getent hosts $TARGET > /dev/null; then PORT=8000; if echo \"$TARGET\" | grep -q \"onrender.com\"; then PORT=80; fi; echo \"[SUCCESS] Backend detectado en: $TARGET:$PORT\"; sed -i \"s|127.0.0.1:9999|$TARGET:$PORT|g\" /etc/nginx/conf.d/default.conf; nginx -s reload; echo \"[DONE] Nginx actualizado y recargado.\"; exit 0; fi; done; echo \"[WAIT] Sin rastro de $B_HOST. Intentando de nuevo... ($i/60)\"; sleep 5; done) & nginx -g 'daemon off;'"]
