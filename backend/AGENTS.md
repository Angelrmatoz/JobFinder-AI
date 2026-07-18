# 🤖 JobFinder AI — Guide for AI Coding Agents (Backend)

Welcome, agent! Read this document carefully before making changes to the Python backend.

---

## Technology Stack & Core Libs
- **Framework**: FastAPI (ASGI) + Uvicorn.
- **Python Version**: 3.10+
- **LLM SDK**: `google-genai` (Modern Gemini client. Do **NOT** use the legacy `google-generativeai` library).
- **APIs**: `apify-client` (Async), `notion-client`.
- **Parsing**: `pypdf` for extracting text from binary PDF data.
- **Testing**: `pytest` + `pytest-asyncio` + `unittest.mock`.

---

## Critical Warnings & Architecture Rules

### 1. Gemini Client & Fallback Chain
- **Do not** instantiate `genai.Client` directly outside of `get_client()` in [gemini_service.py](file:///c:/Dev/Lead-Generation-AI/backend/src/services/gemini_service.py).
- **Do not** call `client.models.generate_content()` directly for business actions. Instead, use the fallback wrapper:
  ```python
  from src.services.gemini_service import generate_content_with_fallback
  # This tries GEMINI_MODEL -> GEMINI_MODEL_FALLBACK_1 -> GEMINI_MODEL_FALLBACK_2 sequentially
  ```
- **Gemini Free-Tier Rate Limits**: The free tier of Gemini has a limit of **15 Requests Per Minute (RPM)**. 
  - To prevent HTTP 429 errors in real integration tests, we enforce a **4-second sleep** (`time.sleep(4)`) between API requests in [test_integration_real.py](file:///c:/Dev/Lead-Generation-AI/backend/tests/test_integration_real.py). Maintain this.

### 2. Notion API Mapping
- Notion requires writing to a **Database ID** (a 32-character hexadecimal string), not a Page ID.
- The columns in the Notion database are case-sensitive and must match these exact property mappings in [notion_service.py](file:///c:/Dev/Lead-Generation-AI/backend/src/services/notion_service.py):
  - `Título` (Type: `title`)
  - `Empresa` (Type: `rich_text`)
  - `Ubicación` (Type: `rich_text`)
  - `Enlace` (Type: `url`)
  - `Match Score` (Type: `number`)
  - `Consejo para Aplicar` (Type: `rich_text`)

### 3. Imports and PyCharm Sources Root
- The root `backend/` must be marked as the **Sources Root** in PyCharm/IntelliJ.
- All internal package imports must be prefixed with `src.`, for example:
  ```python
  from src.schemas.cv import CVProfile
  from src.services.pdf_service import extract_text_from_pdf
  ```

### 4. Pytest Markers
- Do not run real integration tests in standard test cycles. They are marked with `@pytest.mark.integration` and skipped by default.
- Run unit tests: `pytest`
- Run integration tests: `pytest tests/test_integration_real.py --run-integration`

### 5. Dockerization
- The [Dockerfile](file:///c:/Dev/Lead-Generation-AI/backend/Dockerfile) is multi-stage and supports targets `development` (runs Uvicorn with `--reload`) and `production` (runs Uvicorn standard).
- Dedicated compose configurations are located inside the `backend/` directory:
  - **Development**: `docker compose -f docker-compose.dev.yml up --build`
  - **Production**: `docker compose up -d --build`
- In development, the local codebase is mounted to `/app` for hot-reloading.
- The configuration reads `.env` variables from `backend/.env`. Ensure keys are populated.
