# 🤖 JobFinder AI — Guide for AI Coding Agents (Root)

Welcome, agent! This document details the architectural guidelines, technology stack, and critical constraints you must follow when modifying or extending this codebase.

---

## Technical Architecture

JobFinder AI is a Full-Stack application designed to automate job searching:
1. **Frontend**: React 19 + Vite + Tailwind CSS.
2. **Backend**: Python FastAPI service.
3. **External Integrations**: Google AI Studio (Gemini/Gemma), Apify Platform (LinkedIn & Google Jobs Scrapers), Notion API (Databases).

### Apify Scrapers

| Actor | ID | `datePosted` support |
|---|---|---|
| LinkedIn Jobs | `apidojo/linkedin-jobs-scraper` | Native API param |
| Google Jobs | `johnvc/google-jobs-scraper` | **NOT supported** — programmatic only |

**Google Jobs `country` validation**: only `"None", "us", "ca", "uk", "de", "fr", "au", "jp", "in", "br", "mx"` accepted. Unsupported countries (e.g. Spain, Dominican Republic) must map to `"None"` while keeping the correct `google_domain` (e.g. `google.es`).

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
6. **Google Jobs Date Filtering**: Since `johnvc/google-jobs-scraper` ignores `datePosted`, age must be filtered programmatically via `_extract_posted_at` + `_is_within_date_range` in `apify_service.py`. Items with no retrievable age data are rejected when a date filter (`24h`, `7d`, `30d`) is active. Do NOT add `datePosted` to the actor `run_input`.

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
