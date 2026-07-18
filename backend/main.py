import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.routers.jobs import router as jobs_router

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="JobFinder AI API",
    description="Backend modularizado para búsqueda y filtrado de empleo automatizado con Gemini y Apify.",
    version="1.0.0"
)

# Configurar middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar enrutadores
app.include_router(jobs_router)

@app.get("/health")
def health_check():
    """Diagnóstico rápido del estado del servicio y configuraciones de APIs externas."""
    return {
        "status": "online",
        "apis": {
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "apify": bool(os.getenv("APIFY_TOKEN")),
            "notion": bool(os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"))
        }
    }