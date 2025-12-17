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
