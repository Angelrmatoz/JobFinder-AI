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

### 6. Google Jobs Actor Constraints

- Actor ID: **`johnvc/google-jobs-scraper`**
- **`datePosted` is NOT supported** in input schema. Do **not** add it to `run_input`. The Apify actor silently ignores unknown params, causing stale results.
- Date filtering is entirely **programmatic** using helpers in `apify_service.py`:
  - `_extract_posted_at(item)` — reads age text from `posted_at`, `detected_extensions.posted_at`, or `extensions[]` list.
  - `_is_within_date_range(posted_text, date_posted)` — parses bilingual (ES/EN) age strings like `"Hace 2 semanas"` / `"3 days ago"`.
  - If `posted_text` is `None` and a date filter is active (`24h`/`7d`/`30d`), the job is **kept**: absence of a date is not proof of age, and rejecting everything the scraper can't date empties results. Only jobs with a **known** age outside the range are dropped. The `JobDetail.date_posted_unknown` flag is set so the router appends a notice to `apply_tip` telling the user the filter was applied but the posting date couldn't be determined.
  - `_extract_posted_at` only accepts strings that look like relative dates (`_looks_like_date`). Salary noise (e.g. `"3 K por mes"`) is ignored, so it can't shadow a real `detected_extensions.posted_at`.
- **Allowed `country` values**: `"None", "us", "ca", "uk", "de", "fr", "au", "jp", "in", "br", "mx"`. Any other value triggers a schema validation error. Map unsupported countries (e.g. Spain → `"None"`) while keeping the correct `google_domain` (e.g. `google.es`) via `_map_country_and_domain`.
