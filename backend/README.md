# ⚙️ JobFinder AI — Backend Service

Este es el servicio del backend para **JobFinder AI**, construido con **FastAPI** (Python 3.10+). Se encarga de procesar los currículums en PDF, extraer texto, estructurar perfiles profesionales, realizar scraping concurrente en motores de búsqueda de empleo (LinkedIn y Google Jobs), evaluar la afinidad mediante LLMs con resiliencia de fallbacks, y almacenar prospectos idóneos en Notion.

---

## Estructura del Código

```
backend/
├── src/
│   ├── routers/
│   │   └── jobs.py            # Enrutador principal y endpoints (/api/upload-cv, /api/chat)
│   ├── schemas/
│   │   └── cv.py              # Definiciones Pydantic para perfiles, vacantes y respuestas
│   └── services/
│       ├── pdf_service.py     # Lector de PDF local usando pypdf
│       ├── gemini_service.py  # Integración con Google GenAI y cadena de fallbacks
│       ├── apify_service.py   # Consultas concurrentes en Apify (LinkedIn + Google Jobs)
│       └── notion_service.py  # Inserciones estructuradas a la base de datos de Notion
│
├── tests/                     # Suite completa de pruebas automatizadas
│   ├── conftest.py            # Configuración de clientes y fixtures
│   ├── test_endpoints.py      # Pruebas de integración simulada de endpoints FastAPI
│   ├── test_pdf.py            # Pruebas unitarias de lectura de PDF
│   ├── test_gemini.py         # Mocks de Google GenAI
│   ├── test_apify.py          # Mocks de scrapers concurrentes
│   ├── test_notion.py         # Mocks de escritura en Notion
│   └── test_integration_real.py # Pruebas de integración real con APIs de Google y Notion
│
├── main.py                    # Punto de entrada de la aplicación FastAPI y CORS
├── pyproject.toml             # Configuración de pytest y entornos
├── requirements.txt           # Dependencias del backend
└── .env                       # Variables de entorno locales
```

---

## Configuración y Variables de Entorno

Crea el archivo `.env` en este directorio siguiendo la estructura de [.env.template](file:///c:/Dev/Lead-Generation-AI/backend/.env.template):

```env
# Google AI Studio / Gemini API Config
GEMINI_API_KEY=tu_api_key_de_google_ai_studio
GEMINI_MODEL=gemma-4-31b-it
GEMINI_MODEL_FALLBACK_1=gemma-4-26b-a4b-it
GEMINI_MODEL_FALLBACK_2=gemini-3.1-flash-lite

# Apify Scrapers Config
APIFY_TOKEN=tu_api_token_de_apify

# Notion Database Config
NOTION_API_KEY=tu_integration_token_de_notion
NOTION_DATABASE_ID=tu_database_id_32_caracteres
```

---

## Ejecución Local

1. **Crear y activar entorno virtual**:
   ```bash
   python -m venv .venv
   # En Windows:
   .\.venv\Scripts\Activate.ps1
   # En Mac/Linux:
   source .venv/bin/activate
   ```
2. **Instalar dependencias**:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. **Iniciar Servidor**:
   ```bash
   python -m uvicorn main:app --reload
   ```
   El backend estará disponible en `http://localhost:8000`.

---

## Suite de Pruebas

* **Pruebas unitarias (Rápidas, offline y mockeadas)**:
  ```bash
  pytest -v
  ```
* **Pruebas de integración real (Golpea APIs reales, requiere .env configurado)**:
  ```bash
  pytest -v tests/test_integration_real.py --run-integration
  ```
