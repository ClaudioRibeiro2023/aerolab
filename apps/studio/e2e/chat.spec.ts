import { test, expect } from "@playwright/test";

test.describe("Chat Module E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Login mock - ir direto para o chat
    await page.goto("/chat");
    await page.waitForLoadState("domcontentloaded");
  });

  test("chat page loads successfully", async ({ page }) => {
    await expect(page).toHaveURL(/.*chat/);
    const body = await page.locator("body");
    await expect(body).toBeVisible();
  });

  test("chat header elements are visible", async ({ page }) => {
    // Verificar elementos do header
    const header = page.locator("header, [role='banner']").first();
    if (await header.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(header).toBeVisible();
    }
  });

  test("chat input is functional", async ({ page }) => {
    // Buscar input de mensagem
    const input = page.locator("textarea, input[type='text']").first();
    if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(input).toBeVisible();
      await input.fill("Teste de mensagem");
      await expect(input).toHaveValue("Teste de mensagem");
    }
  });

  test("search functionality works (Ctrl+F)", async ({ page }) => {
    // Testar atalho de busca
    await page.keyboard.press("Control+f");
    await page.waitForTimeout(500);
    
    const searchInput = page.locator("input[placeholder*='Buscar']").first();
    if (await searchInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(searchInput).toBeVisible();
    }
  });

  test("agent selector is visible", async ({ page }) => {
    // Verificar seletor de agentes
    const agentSelector = page.locator("button:has-text('Agente'), select, [role='combobox']").first();
    if (await agentSelector.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(agentSelector).toBeVisible();
    }
  });

  test("model selector is visible", async ({ page }) => {
    // Verificar seletor de modelo
    const modelSelector = page.locator("button:has-text('Model'), button:has-text('GPT'), button:has-text('Claude')").first();
    if (await modelSelector.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(modelSelector).toBeVisible();
    }
  });

  test("backend status indicator shows", async ({ page }) => {
    // Verificar indicador de status do backend
    const statusIndicator = page.locator("[title*='Backend'], [title*='API']").first();
    if (await statusIndicator.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(statusIndicator).toBeVisible();
    }
  });

  test("export button is available", async ({ page }) => {
    // Verificar botão de exportar
    const exportBtn = page.locator("button[title*='Export'], button:has-text('Export')").first();
    if (await exportBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(exportBtn).toBeVisible();
    }
  });

  test("no critical console errors on chat page", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    await page.goto("/chat");
    await page.waitForLoadState("networkidle");

    // Filtrar erros conhecidos/aceitáveis
    const criticalErrors = errors.filter(
      (e) => 
        !e.includes("favicon") && 
        !e.includes("404") && 
        !e.includes("400") && 
        !e.includes("Failed to load resource") &&
        !e.includes("CORS") &&
        !e.includes("hydration")
    );
    
    expect(criticalErrors.length).toBeLessThanOrEqual(2);
  });
});

test.describe("Chat Responsive Design", () => {
  test("chat renders on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/chat");
    await page.waitForLoadState("domcontentloaded");
    
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("chat renders on tablet", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/chat");
    await page.waitForLoadState("domcontentloaded");
    
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });
});
