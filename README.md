# 🎯 JobFinder AI — Automatización de Búsqueda de Empleo

> **JobFinder AI** — Automatiza por completo la búsqueda, filtrado y almacenamiento de ofertas de trabajo personalizadas a partir de tu currículum.

---

## ¿Qué es esto?

JobFinder AI es una aplicación web Full-Stack diseñada para eliminar la búsqueda manual de empleo. Subes tu currículum en formato PDF desde el frontend; el sistema extrae tu perfil profesional de forma inteligente, busca vacantes reales en internet en tiempo real, las evalúa según su afinidad y guarda automáticamente las mejores opciones en Notion.

**El flujo de procesamiento consiste en:**
1. **Frontend (React):** Interfaz limpia y premium con componente *Drag & Drop* para subir el archivo PDF del currículum. 
   - **Exclusividad en Filtros**: El selector geográfico gestiona dinámicamente las modalidades; al elegir la búsqueda "Global / Sin país", se deshabilitan las opciones híbrida y presencial, y se fuerza el formato "Remoto".
   - **Idiomas Inteligentes**: Los botones de idioma son mutuamente excluyentes (Español o Inglés), y al intentar marcar ambos, se colapsa automáticamente a la opción "Cualquiera" para evitar redundancias.
2. **Backend (FastAPI):**
   - Recibe el PDF y extrae el texto plano usando la librería `pypdf`.
   - **Interpretación**: Envía el texto a **Gemini** en Google AI Studio (mediante el SDK `google-genai`) para estructurar el perfil (`CVProfile`) y generar una query de búsqueda optimizada.
   - **Traducción y Búsqueda Multilingüe**: Si se selecciona filtrar por Español, el backend traduce automáticamente los roles de búsqueda del CV a español antes de solicitar a Apify, incrementando las coincidencias de puestos hispanohablantes.
   - **Scraping (Apify) con Filtro Temprano**: Llama a los actores públicos de Apify. Durante el procesamiento de los resultados, se realiza un descarte de idioma programático basado en stopwords *antes* de aplicar el límite de corte (15 vacantes), asegurando que el listado final se llene únicamente con vacantes del idioma seleccionado.
   - **Filtro Cognitivo (Doble Capa)**: Evalúa la afinidad de cada vacante mediante Gemini. Si se definió una modalidad estricta (ej: solo remoto) y la descripción del puesto indica que es híbrido o presencial, la IA asignará automáticamente un *Match Score* de `1/10` y descartará la vacante.
   - **Almacenamiento**: Las ofertas con un Match Score mayor a 7 se guardan automáticamente en una base de datos de **Notion** usando `notion-client`.
   - **Resiliencia (Model Fallback)**: Implementa una cadena de reintentos automática (`gemma-4-31b-it` -> `gemma-4-26b-a4b-it` -> `gemini-3.1-flash-lite`) para asegurar la disponibilidad del servicio y mitigar límites de cuotas/RPM.
   - **Asesor de Carrera**: Permite chatear interactivamente sobre el perfil o las vacantes encontradas mediante un chat integrado con formateador seguro de negritas en Markdown.
3. **Scraping Dual (LinkedIn + Google Jobs)**:
    - **LinkedIn** (`apidojo/linkedin-jobs-scraper`): Soporta `datePosted` nativo como parámetro de API.
    - **Google Jobs** (`johnvc/google-jobs-scraper`): El actor **no** soporta `datePosted` en su schema de entrada. El filtro de fecha se aplica **programáticamente** en backend leyendo el texto de antigüedad (`detected_extensions.posted_at`, `extensions[]`, `posted_at`) en español e inglés (ej. `"Hace 2 semanas"`, `"3 days ago"`). Trabajos sin dato de antigüedad se descartan si hay filtro de fecha activo.

---

## Estructura del Proyecto

```
Lead-Generation-AI/ (JobFinder AI)
├── backend/                   # Servidor FastAPI
│   ├── src/
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
│   │   ├── components/        # Badge, ChatPanel, LoadingPulse, ResultsPanel, Section
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── pnpm-lock.yaml
│
├── docker-compose.yml         # Stack completo (producción)
├── docker-compose.dev.yml     # Stack completo (desarrollo con hot-reload)
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

El proyecto incluye una suite completa de pruebas automatizadas para backend y frontend.

### 1. Backend (Pytest)

Las pruebas del backend incluyen pruebas unitarias offline (con mocks) y de integración real.

* **Ejecutar pruebas unitarias locales (rápidas, offline, 0 costo):**
  ```bash
  cd backend
  ..\.venv\Scripts\pytest -v
  ```
* **Ejecutar pruebas de integración con las APIs reales (Gemini y Notion):**
  ```bash
  cd backend
  ..\.venv\Scripts\pytest -v tests/test_integration_real.py --run-integration
  ```

### 2. Frontend (Vitest & Playwright)

El frontend modular cuenta con pruebas unitarias, de integración y de extremo a extremo (E2E).

* **Ejecutar pruebas unitarias e integración de componentes (Vitest):**
  ```bash
  cd frontend
  pnpm test run
  ```
* **Ejecutar pruebas E2E en navegadores reales (Playwright):**
  ```bash
  cd frontend
  # Instala los navegadores necesarios (la primera vez)
  pnpm exec playwright install
  # Corre las pruebas E2E
  pnpm test:e2e
  ```

---

## Docker (recomendado)

Puedes levantar el stack completo sin instalar Python ni Node localmente.

### Stack completo

```bash
# Desarrollo (hot-reload)
docker compose -f docker-compose.dev.yml up --build

# Producción
docker compose up -d --build
```

### Servicios individuales

```bash
# Solo backend
cd backend
docker compose -f docker-compose.dev.yml up --build

# Solo frontend
cd frontend
docker compose -f docker-compose.dev.yml up --build
```

> **Importante:** Asegúrate de que `backend/.env` esté correctamente configurado antes de levantar cualquier servicio.

---

## Integración Continua (CI/CD)

El proyecto cuenta con un flujo de **GitHub Actions** configurado en [.github/workflows/ci.yml](file:///.github/workflows/ci.yml). Este pipeline se ejecuta en cada *push* o *Pull Request* hacia las ramas `dev` y `main`, garantizando de forma automatizada que:
1. El backend pase todas sus pruebas unitarias.
2. El frontend pase todas las pruebas unitarias y de integración en Vitest.
3. Se ejecuten las pruebas de Playwright de extremo a extremo en navegadores reales de forma segura e independiente sin costos de API (utilizando interceptores de red).

---