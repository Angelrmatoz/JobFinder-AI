# 🎯 JobFinder AI — Automatización de Búsqueda de Empleo

> **JobFinder AI** — Automatiza por completo la búsqueda, filtrado y almacenamiento de ofertas de trabajo personalizadas a partir de tu currículum.

---

## ¿Qué es esto?

JobFinder AI es una aplicación web Full-Stack diseñada para eliminar la búsqueda manual de empleo. Subes tu currículum en formato PDF desde el frontend; el sistema extrae tu perfil profesional de forma inteligente, busca vacantes reales en internet en tiempo real, las evalúa según su afinidad y guarda automáticamente las mejores opciones en Notion.

**El flujo de procesamiento consiste en:**
1. **Frontend (React):** Interfaz limpia con componente *Drag & Drop* para subir el archivo PDF del currículum.
2. **Backend (FastAPI):**
   - Recibe el PDF y extrae el texto plano usando la librería `pypdf`.
   - **Interpretación**: Envía el texto a **Gemini** en Google AI Studio (mediante el SDK `google-genai`) para estructurar el perfil (`CVProfile`) y generar una query de búsqueda optimizada (ej. `"React Developer remote junior"`).
   - **Scraping (Apify)**: Llama concurrentemente en paralelo a los actores públicos **LinkedIn Jobs Scraper** y **Google Jobs Scraper** para consolidar vacantes.
   - **Filtro Cognitivo**: Evalúa la afinidad de cada vacante con el perfil del candidato, calcula un *Match Score* (1 a 10) y redacta un consejo para aplicar a cada vacante.
   - **Almacenamiento**: Las ofertas con un Match Score mayor a 7 se guardan automáticamente en una base de datos de **Notion** usando `notion-client`.
   - **Asesor de Carrera**: Permite chatear interactivamente sobre el perfil o las vacantes encontradas mediante un chat integrado.

---

## Estructura del Proyecto

```
Lead-Generation-AI/ (JobFinder AI)
├── backend/                   # Servidor FastAPI
│   ├── app/
│   │   ├── routers/           # Enrutadores de endpoints (jobs.py)
│   │   ├── schemas/           # Validaciones Pydantic (cv.py)
│   │   └── services/          # Servicios externos (pdf, gemini, apify, notion)
│   ├── tests/                 # Suite de pruebas automatizadas con pytest
│   ├── main.py                # Punto de entrada modular de FastAPI
│   ├── requirements.txt       # Dependencias del Backend
│   └── .env                   # Variables de entorno locales
│
├── frontend/                  # Interfaz de Usuario React
│   ├── src/
│   │   ├── App.jsx            # Interfaz principal (Drag & Drop + Resultados + Chat)
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── pnpm-lock.yaml
│
└── README.md
```

---

## Configuración y Ejecución Local

### Prerrequisitos
- Node.js 18+ y `pnpm` instalado.
- Python 3.10+ instalado.
- Apify account con API token ([apify.com](https://apify.com))
- Google AI Studio API key ([aistudio.google.com](https://aistudio.google.com))
- Notion Integration Token y base de datos configurada ([developers.notion.com](https://developers.notion.com))

### 1. Clonar el repositorio e instalar dependencias

```bash
git clone https://github.com/Angelrmatoz/Lead-Generation-AI.git
cd Lead-Generation-AI
```

### 2. Configurar y Ejecutar el Backend

1. Entra a la carpeta de backend y activa tu entorno virtual:
   ```bash
   cd backend
   # Activa tu entorno virtual (.venv) autogenerado
   .\.venv\Scripts\Activate.ps1
   ```
2. Instala las dependencias:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Configura el archivo `backend/.env` con tus llaves reales:
   ```env
   # Google AI Studio / Gemini API Config
   GEMINI_API_KEY=tu_api_key_de_gemini
   GEMINI_MODEL=gemini-2.5-flash

   # Apify Scrapers Config
   APIFY_TOKEN=tu_token_de_apify

   # Notion Database Config
   NOTION_API_KEY=tu_token_de_integracion_notion
   NOTION_DATABASE_ID=tu_id_de_base_de_datos_notion
   ```
4. Corre el servidor local:
   ```bash
   python -m uvicorn main:app --reload
   ```

### 3. Configurar y Ejecutar el Frontend

1. Abre una nueva terminal en la carpeta `frontend/`:
   ```bash
   cd frontend
   pnpm install
   pnpm run dev
   ```
2. Abre tu navegador en: `http://localhost:5173`

---

## Pruebas Automatizadas

El proyecto incluye una suite completa de pruebas unitarias (con mocks) y de integración real.

**Ejecutar pruebas unitarias locales (rápidas, offline, 0 costo):**
```bash
cd backend
..\.venv\Scripts\pytest -v
```

**Ejecutar pruebas de integración con las APIs reales (Gemini y Notion):**
```bash
cd backend
..\.venv\Scripts\pytest -v tests/test_integration_real.py --run-integration
```

---

## Licencia

MIT — libre de usar, modificar y construir sobre él.