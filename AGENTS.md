# 🤖 JobFinder AI — Guide for AI Coding Agents (Root)

Welcome, agent! This document details the architectural guidelines, technology stack, and critical constraints you must follow when modifying or extending this codebase.

---

## Technical Architecture

JobFinder AI is a Full-Stack application designed to automate job searching:
1. **Frontend**: React 19 + Vite + Tailwind CSS.
2. **Backend**: Python FastAPI service.
3. **External Integrations**: Google AI Studio (Gemini/Gemma), Apify Platform (LinkedIn & Google Jobs Scrapers), Notion API (Databases).

### Apify Scrapers

Default IDs live in `apify_service.py` and are overridable by env var. Do not hardcode actor IDs elsewhere.

| Actor | Default ID (env override) | Date filtering |
|---|---|---|
| LinkedIn Jobs | `valig/linkedin-jobs-scraper` (`LINKEDIN_ACTOR_ID`) | Native API param `datePosted` (`r86400`/`r604800`/`r2592000`) |
| Google Jobs | `inovaflow/google-jobs-scraper` (`GOOGLE_ACTOR_ID`) | Native API param `postedWithin` (`day`/`3days`/`week`/`month`) |

**Google Jobs `country` validation**: only two-letter Google editions from the actor enum (e.g. `us`, `gb`, `es`, `mx`, `co`, `ar`, `cl`, `de`, `fr`, `au`, `jp`, `in`) are accepted. `_map_country` resolves location/language to a valid code and never sends `"None"`; unsupported countries fall back to `us` (or `es` when the target language is Spanish).

---

## Coding Rules & Guidelines

1. **Modular Architecture**: 
   - Backend logic must remain separated into schemas and isolated services (`pdf`, `gemini`, `apify`, `notion`).
   - Frontend components must remain modular in `src/components/`. Do not bloat `App.jsx`.
2. **Test Suites Integrity**:
   - Every feature must include corresponding tests.
   - **Backend**: Unit tests must be 100% offline (mocked). Real integration tests must use the `@pytest.mark.integration` marker so they are skipped by default.
   - **Frontend**: Unit tests use Vitest + jsdom. E2E tests use Playwright with intercepted API routes.
3. **No Placeholders**: Never commit placeholders or incomplete code. Always supply full, operational implementations.
4. **Resiliency**: The Gemini service implements a fallback chain. Do not hardcode a single model name; use the fallback utility.
5. **Multilingual & Modality Filtering**: Early language checking (using programmatic stopword helpers) must be enforced before evaluating scraping limits, and strict double-layer modality restrictions (both in scraper API params and Gemini prompts) must be maintained to avoid misclassified jobs receiving high match scores.
6. **Google Jobs Date Filtering**: `inovaflow/google-jobs-scraper` applies `postedWithin` natively (`24h` → `day`, `7d` → `week`, `30d` → `month`). Do NOT add `datePosted` or filter ages programmatically. The actor keeps items with no stated age, so those get `date_posted_unknown = True` for the router notice.

---

## Global Directory Overview

- [.github/workflows/ci.yml](file:///c:/Dev/Lead-Generation-AI/.github/workflows/ci.yml): Runs unit & E2E tests on push/PR.
- [backend/](file:///c:/Dev/Lead-Generation-AI/backend/): FastAPI service, requirements, and pytest suite.
- [frontend/](file:///c:/Dev/Lead-Generation-AI/frontend/): React UI, vitest configurations, and playwright tests.

---

## Docker Stack Guidelines

You can run the entire stack together or manage services individually:

- **Running Stack Jointly**:
  - **Development**:
    ```bash
    docker compose -f docker-compose.dev.yml up --build
    ```
  - **Production**:
    ```bash
    docker compose up -d --build
    ```

- **Running Backend Individually**:
  - Go to `backend/` and run:
    - **Development**: `docker compose -f docker-compose.dev.yml up --build`
    - **Production**: `docker compose up -d --build`

- **Running Frontend Individually**:
  - Go to `frontend/` and run:
    - **Development**: `docker compose -f docker-compose.dev.yml up --build`
    - **Production**: `docker compose up -d --build`

- Ensure `backend/.env` is correctly populated before starting.
