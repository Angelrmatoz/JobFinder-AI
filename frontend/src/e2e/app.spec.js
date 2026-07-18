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
