# syntax=docker/dockerfile:1

# --- Etapa 1: Base (Instalación de Node y Dependencias) ---
FROM node:24-alpine@sha256:6a1c190e17215d844926b0677f4bf87273ff7d5e54db06d3b5b5863ab0b09a3d AS base

WORKDIR /app

# Instalar pnpm en la misma versión usada para generar el lockfile
ENV PNPM_HOME="/pnpm" \
    PATH="$PNPM_HOME:$PATH" \
    CI=true
RUN npm install -g pnpm@12.8.1

# Copiar archivos de dependencias
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml /app/

# Instalar dependencias usando caché mount de BuildKit y lockfile inmutable
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile

# Copiar el código del frontend
COPY . /app/

# --- Etapa 2: Desarrollo (Vite Dev Server) ---
FROM base AS development
EXPOSE 5173
# Ejecutar servidor de desarrollo con recarga en caliente
CMD ["pnpm", "exec", "vite", "--host", "0.0.0.0", "--port", "5173"]

# --- Etapa 3: Compilación para Producción ---
FROM base AS builder
# Compilar los estáticos a la carpeta /app/dist
RUN pnpm build

# --- Etapa 4: Servidor Nginx de Producción (sin privilegios) ---
FROM nginxinc/nginx-unprivileged:alpine@sha256:b5047b9b76845eac124358373c6852377c52e4b05834a47647e955dd91cb8f1e AS production
# Copiar estáticos compilados
COPY --from=builder /app/dist /usr/share/nginx/html
# Copiar la configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "--spider", "http://127.0.0.1:8080/"]
CMD ["nginx", "-g", "daemon off;"]
