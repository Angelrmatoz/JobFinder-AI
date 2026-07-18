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
- **pnpm-workspace.yaml**:
  - `packages`: Must list `.` to be recognized as a valid workspace so configuration is loaded.
  - `minimumReleaseAge: 0`: Disables pnpm 11's default 24-hour cooling-off security checks, preventing false-positive package age blocks.
  - `allowBuilds`: Explicitly allows `esbuild` to run its installation build script. This is required by pnpm 11+ which blocks all build scripts by default and replaces the legacy `onlyBuiltDependencies` configuration.
  - `nodeLinker: hoisted` and `packageImportMethod: copy`: Forces a flat/hoisted `node_modules` structure and physically copies packages instead of symlinking/hardlinking them. This prevents broken symlinks in Docker containers when BuildKit store cache is unmounted.
- **Docker Caching**: We use a BuildKit cache mount (`--mount=type=cache,id=pnpm,target=/pnpm/store`) in the [Dockerfile](file:///c:/Dev/Lead-Generation-AI/frontend/Dockerfile) to persist the pnpm store across builds. This prevents redownloading packages when `package.json` changes.

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

### 4. Vitest and Playwright File Collision
- Since Playwright E2E tests (`src/e2e/**`) end in `.spec.js`, Vitest will attempt to run them as unit tests and fail (due to `@playwright/test` imports).
- The `src/e2e/**` folder must be explicitly excluded in `vite.config.js` (`exclude: [...configDefaults.exclude, "src/e2e/**"]`).

### 5. Component Modularization
- Do not bloat `App.jsx`. Sub-components must reside in `src/components/` (e.g. `Badge.jsx`, `ChatPanel.jsx`, `ResultsPanel.jsx`).
- Pass coordination callbacks or data states down from `App.jsx`.

### 6. Dockerization & Dynamic API Path
- The [Dockerfile](file:///c:/Dev/Lead-Generation-AI/frontend/Dockerfile) is multi-stage and supports targets `development` (runs Vite dev server on `5173`) and `production` (compiles and serves with **Nginx** on `80`).
- Dedicated compose configurations are located inside the `frontend/` directory:
  - **Development**: `docker compose -f docker-compose.dev.yml up --build`
  - **Production**: `docker compose up -d --build`
- In development, only source files and configurations are mounted (`src/`, `index.html`, `vite.config.js`) to allow hot-reloading while preventing local Windows node_modules symlinks from colliding with the Linux container node_modules.
- Nginx proxies `/api/*` requests internally to the backend container.
- To support this proxy, the `API` path in `App.jsx` is defined dynamically:
  ```javascript
  const API = import.meta.env.DEV ? "http://localhost:8000" : "";
  ```
  Keep the API endpoint path relative (`""`) in production so it targets the Nginx reverse-proxy correctly on any host.
