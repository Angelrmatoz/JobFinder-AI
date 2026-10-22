# syntax=docker/dockerfile:1

# --- Etapa Base ---
FROM python:3.11-slim@sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8 AS base

# Evitar que Python escriba archivos .pyc en disco y habilitar logs sin búfer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias primero para aprovechar la caché de Docker.
# Todas las dependencias tienen wheel para cp311, no se necesita build-essential.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend a la imagen
COPY . /app/

# Exponer el puerto de FastAPI
EXPOSE 8000

# --- Etapa Desarrollo ---
FROM base AS development
# Comando para desarrollo con recarga en caliente (--reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Etapa Producción ---
FROM base AS production

# Ejecutar como usuario sin privilegios
RUN useradd --uid 10001 --create-home app && chown -R app:app /app
USER 10001

# El pipeline de scraping + matching puede tardar más que un health check normal
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]

# Detrás de nginx: confiar en X-Forwarded-* para IP y scheme del cliente
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
