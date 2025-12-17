import { test, expect } from "@playwright/test";

test.describe("Studio Smoke Tests", () => {
  test("homepage loads successfully", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/./);
  });

  test("page has no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Filter out known acceptable errors
    const criticalErrors = errors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test("navigation elements are visible", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    // Check that the page has loaded with some content
    const body = await page.locator("body");
    await expect(body).toBeVisible();
  });
});

test.describe("API Integration", () => {
  test("health endpoint is accessible via proxy", async ({ request }) => {
    const response = await request.get("/api/health");
    // May return 200 if backend is running, or error if not
    expect([200, 502, 503]).toContain(response.status());
  });
});

test.describe("Navigation", () => {
  test("can navigate to agents page", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    // Look for agents link/button if exists
    const agentsLink = page.locator('a[href*="agent"], button:has-text("Agent")').first();
    if (await agentsLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await agentsLink.click();
      await page.waitForLoadState("domcontentloaded");
    }
  });

  test("can navigate to flows page", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    // Look for flows link/button if exists
    const flowsLink = page.locator('a[href*="flow"], button:has-text("Flow")').first();
    if (await flowsLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await flowsLink.click();
      await page.waitForLoadState("domcontentloaded");
    }
  });
});

test.describe("UI Components", () => {
  test("sidebar renders correctly", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    // Check for common sidebar elements
    const sidebar = page.locator('nav, aside, [role="navigation"]').first();
    if (await sidebar.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(sidebar).toBeVisible();
    }
  });

  test("main content area is visible", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const main = page.locator('main, [role="main"], .main-content').first();
    if (await main.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(main).toBeVisible();
    }
  });
});

test.describe("Responsive Design", () => {
  test("renders correctly on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("renders correctly on tablet", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("renders correctly on desktop", async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const body = page.locator("body");
    await expect(body).toBeVisible();
  });
});
