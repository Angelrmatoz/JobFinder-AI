# --- Etapa Base ---
FROM python:3.11-slim AS base

# Evitar que Python escriba archivos .pyc en disco y habilitar logs sin búfer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar herramientas del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias primero para aprovechar la caché de Docker
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
# Comando para producción sin reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
