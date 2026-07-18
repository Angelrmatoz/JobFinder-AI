# 🤖 JobFinder AI — Guide for AI Coding Agents (Root)

Welcome, agent! This document details the architectural guidelines, technology stack, and critical constraints you must follow when modifying or extending this codebase.

---

## Technical Architecture

JobFinder AI is a Full-Stack application designed to automate job searching:
1. **Frontend**: React 19 + Vite + Tailwind CSS.
2. **Backend**: Python FastAPI service.
3. **External Integrations**: Google AI Studio (Gemini/Gemma), Apify Platform (LinkedIn & Google Jobs Scrapers), Notion API (Databases).

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

---

## Global Directory Overview

- [.github/workflows/ci.yml](file:///c:/Dev/Lead-Generation-AI/.github/workflows/ci.yml): Runs unit & E2E tests on push/PR.
- [backend/](file:///c:/Dev/Lead-Generation-AI/backend/): FastAPI service, requirements, and pytest suite.
- [frontend/](file:///c:/Dev/Lead-Generation-AI/frontend/): React UI, vitest configurations, and playwright tests.
