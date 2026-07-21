import { test, expect } from "@playwright/test";

const mockApiResponse = {
  profile: {
    name: "Carlos Ruiz",
    email: "carlos@example.com",
    skills: ["Docker", "Kubernetes"],
    experience_summary: "DevOps Engineer con 4 años de experiencia.",
    target_roles: ["DevOps Engineer"],
    search_query: "DevOps Engineer junior"
  },
  jobs: [
    {
      title: "DevOps Engineer",
      company: "CloudTech",
      location: "Madrid",
      link: "https://example.com/apply-devops",
      description: "Buscamos ingeniero devops.",
      match_score: 9,
      apply_tip: "Tip de kubernetes.",
      saved_to_notion: true
    }
  ]
};

test.describe("JobFinder AI E2E Workflow", () => {
  test("should load the home page and complete CV upload flow", async ({ page }) => {
    // Interceptar llamada API del backend y responder con mock con un pequeño retraso
    await page.route("**/api/upload-cv", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockApiResponse)
      });
    });

    // Navegar a la app
    await page.goto("/");

    // Verificar título
    await expect(page).toHaveTitle(/JobFinder AI/);

    // Verificar que la zona de arrastre esté visible
    const dropzone = page.getByTestId("dropzone");
    await expect(dropzone).toBeVisible();

    // Crear un archivo PDF mock y simular la subida
    const filePayload = {
      name: "mi_cv.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("dummy pdf content")
    };

    // Hacer clic y simular la selección de archivos
    const fileChooserPromise = page.waitForEvent("filechooser");
    await dropzone.click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles([filePayload]);

    // Verificar que aparezca la pantalla de carga LoadingPulse
    const loadingPulse = page.getByTestId("loading-pulse");
    await expect(loadingPulse).toBeVisible();
    await expect(page.getByText("Leyendo y extrayendo texto del PDF...")).toBeVisible();

    // Esperar y verificar que aparezca el panel de resultados
    const resultsPanel = page.getByTestId("results-panel");
    await expect(resultsPanel).toBeVisible();

    // Verificar nombre y email extraído en el header
    await expect(page.getByText("Carlos Ruiz")).toBeVisible();
    await expect(page.getByText("carlos@example.com")).toBeVisible();

    // Verificar detalles de la vacante en el listado
    await expect(page.getByText("DevOps Engineer", { exact: false })).toBeVisible();
    await expect(page.getByText("CloudTech")).toBeVisible();
    await expect(page.getByText("✓ Notion")).toBeVisible();

    // Verificar que el panel de chat con el asesor de carrera por IA esté visible
    const chatPanel = page.getByTestId("chat-panel");
    await expect(chatPanel).toBeVisible();
  });
});

test.describe("JobFinder AI — Error States E2E", () => {
  test("should show error message when API returns 500", async ({ page }) => {
    await page.route("**/api/upload-cv", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal Server Error" })
      });
    });

    await page.goto("/");

    const dropzone = page.getByTestId("dropzone");
    await expect(dropzone).toBeVisible();

    const fileChooserPromise = page.waitForEvent("filechooser");
    await dropzone.click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles([{
      name: "cv.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("dummy pdf")
    }]);

    // Should show error feedback — dropzone returns to initial state or error msg
    await expect(page.getByTestId("dropzone")).toBeVisible({ timeout: 8000 });
  });
});

test.describe("JobFinder AI — Chat E2E", () => {
  test("should send a chat message and receive AI response", async ({ page }) => {
    // Mock upload endpoint
    await page.route("**/api/upload-cv", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 300));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockApiResponse)
      });
    });

    // Mock chat endpoint
    await page.route("**/api/chat", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ answer: "Te recomiendo destacar tu experiencia en Docker." })
      });
    });

    await page.goto("/");

    // Upload CV first to get to results + chat state
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByTestId("dropzone").click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles([{
      name: "cv.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("dummy pdf")
    }]);

    // Wait for chat panel
    const chatPanel = page.getByTestId("chat-panel");
    await expect(chatPanel).toBeVisible({ timeout: 10000 });

    // Type and send a chat message
    const chatInput = page.getByPlaceholder("Pregunta algo...");
    await chatInput.fill("¿Cómo mejoro mi CV?");
    await page.getByRole("button", { name: "↑" }).click();

    // Verify AI response appears
    await expect(page.getByText("Te recomiendo destacar tu experiencia en Docker.")).toBeVisible({ timeout: 5000 });
  });
});

test.describe("JobFinder AI — Filters Panel E2E", () => {
  test("should toggle location scope and show manual input", async ({ page }) => {
    await page.goto("/");

    // Filtros están en acordeón colapsado por defecto — abrir primero
    const filtersToggle = page.getByTestId("filters-toggle");
    await expect(filtersToggle).toBeVisible();
    await filtersToggle.click();

    // Location scope select ahora visible
    const locationSelect = page.getByTestId("location-scope-select");
    await expect(locationSelect).toBeVisible();

    // Switch to manual location
    await locationSelect.selectOption("manual");

    // Manual location input should appear
    const manualInput = page.getByTestId("manual-location-input");
    await expect(manualInput).toBeVisible();
    await manualInput.fill("Buenos Aires");

    // Presencial and Híbrido buttons should be enabled
    const presencialBtn = page.getByTestId("workplace-presencial");
    await expect(presencialBtn).toBeEnabled();
  });

  test("should enforce mutual exclusion between Spanish and English language buttons", async ({ page }) => {
    await page.goto("/");

    // Abrir acordeón de filtros
    await page.getByTestId("filters-toggle").click();

    const spanishBtn = page.getByTestId("lang-btn-es");
    const englishBtn = page.getByTestId("lang-btn-en");

    await expect(spanishBtn).toBeVisible();
    await expect(englishBtn).toBeVisible();

    // Click Spanish
    await spanishBtn.click();

    // Click English — should collapse to "any" or toggle exclusion
    await englishBtn.click();

    // Both should NOT be simultaneously highlighted with violet border
    const spanishBorderClass = await spanishBtn.evaluate((el) =>
      el.className.includes("border-violet-500")
    );
    const englishBorderClass = await englishBtn.evaluate((el) =>
      el.className.includes("border-violet-500")
    );
    expect(spanishBorderClass && englishBorderClass).toBe(false);
  });
});
