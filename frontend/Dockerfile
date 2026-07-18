# --- Etapa 1: Base (Instalación de Node y Dependencias) ---
FROM node:24-alpine AS base

WORKDIR /app

# Instalar pnpm de manera global y configurar directorios
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN npm install -g pnpm

# Copiar archivos de dependencias
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* /app/

# Instalar dependencias usando caché mount de BuildKit para evitar descargas repetidas
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --no-frozen-lockfile

# Copiar el código del frontend
COPY . /app/

# --- Etapa 2: Desarrollo (Vite Dev Server) ---
FROM base AS development
EXPOSE 5173
# Ejecutar servidor de desarrollo con recarga en caliente
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]

# --- Etapa 3: Compilación para Producción ---
FROM base AS builder
# Compilar los estáticos a la carpeta /app/dist
RUN pnpm build

# --- Etapa 4: Servidor Nginx de Producción ---
FROM nginx:alpine AS production
# Copiar estáticos compilados
COPY --from=builder /app/dist /usr/share/nginx/html
# Copiar la configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
