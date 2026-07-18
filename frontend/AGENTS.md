# 🤖 JobFinder AI — Guide for AI Coding Agents (Frontend)

Welcome, agent! Read this document carefully before making changes to the React frontend.

---

## Technology Stack
- **Framework**: React 19 + Vite (ES modules).
- **Styling**: Vanilla CSS (Tailwind CSS loaded from CDN in `index.html`).
- **HTTP Client**: Axios (imported and exported as `axiosInstance` to point to `http://localhost:8000`).
- **Testing**: Vitest + React Testing Library (RTL) + jsdom.
- **E2E Testing**: Playwright (runs tests against Chromium & Webkit).

---

## Critical Warnings & Architecture Rules

### 1. Package Manager & Script Executions
- This workspace is configured to use **pnpm** as the package manager.
- **Windows Restriction Warning**: On Windows machines with restricted script execution policies, running `pnpm` directly in PowerShell can trigger security blocks. Always invoke it via `pnpm.cmd` or run inside `cmd` shells.
  - Script for dev: `pnpm run dev`
  - Script for unit tests: `pnpm test run`
  - Script for E2E tests: `pnpm test:e2e`

### 2. jsdom layout restrictions (scrollIntoView)
- The unit test environment uses **jsdom**, which does not feature a layout engine.
- Layout-dependent methods like `Element.scrollIntoView()` are **not** defined.
- To prevent test failures:
  - Check if the method exists in code before calling it:
    ```javascript
    if (element?.scrollIntoView) {
      element.scrollIntoView({ behavior: "smooth" });
    }
    ```
  - A global fallback is mocked in [setupTests.js](file:///c:/Dev/Lead-Generation-AI/frontend/src/setupTests.js):
    ```javascript
    window.HTMLElement.prototype.scrollIntoView = function() {};
    ```

### 3. Playwright E2E Mocking and Timing
- The E2E tests are configured in `src/e2e/app.spec.js`.
- The backend API call `/api/upload-cv` is mocked using Playwright's `page.route()`.
- To allow verifying the loading spinner (`LoadingPulse` showing *"Leyendo y extrayendo texto del PDF..."*), the mock must enforce a delay:
  ```javascript
  await page.route("**/api/upload-cv", async (route) => {
    // Delays response by 500ms to avoid instant transitions
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.fulfill({ ... });
  });
  ```
- Make sure to update the mock delay if adding other async steps.

### 4. Component Modularization
- Do not bloat `App.jsx`. Sub-components must reside in `src/components/` (e.g. `Badge.jsx`, `ChatPanel.jsx`, `ResultsPanel.jsx`).
- Pass coordination callbacks or data states down from `App.jsx`.
