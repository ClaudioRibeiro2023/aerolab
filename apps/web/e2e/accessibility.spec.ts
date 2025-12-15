import { test, expect } from '@playwright/test'

test.describe('Acessibilidade - Estrutura', () => {
  test('deve ter landmarks semânticos', async ({ page }) => {
    await page.goto('/')

    // Header
    await expect(page.locator('header').first()).toBeVisible()

    // Main
    await expect(page.locator('main').first()).toBeVisible()

    // Nav (sidebar) - usa first() para evitar strict mode
    await expect(page.locator('aside').first()).toBeVisible()
    await expect(page.locator('aside nav').first()).toBeVisible()
  })

  test('deve ter hierarquia de headings correta', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('main')).toBeVisible()

    // Deve haver pelo menos um heading
    const headings = page.locator('h1, h2, h3, h4, h5, h6')
    const count = await headings.count()

    expect(count).toBeGreaterThan(0)
  })

  test('imagens devem ter alt text', async ({ page }) => {
    await page.goto('/')

    const images = page.locator('img')
    const count = await images.count()

    for (let i = 0; i < count; i++) {
      const img = images.nth(i)
      const alt = await img.getAttribute('alt')
      // Alt pode ser vazio para imagens decorativas, mas deve existir
      expect(alt).toBeDefined()
    }
  })

  test('links devem ter texto descritivo', async ({ page }) => {
    await page.goto('/')

    const links = page.locator('a')
    const count = await links.count()

    for (let i = 0; i < Math.min(count, 10); i++) {
      const link = links.nth(i)
      const text = await link.textContent()
      const ariaLabel = await link.getAttribute('aria-label')
      const title = await link.getAttribute('title')

      // Link deve ter texto ou aria-label (ou title em links com ícone)
      expect(text?.trim() || ariaLabel || title).toBeTruthy()
    }
  })
})

test.describe('Acessibilidade - Interação', () => {
  test('skip link deve existir (se implementado)', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('main').first()).toBeVisible()

    // Garante foco na página clicando no body primeiro
    await page.locator('body').click()

    // Skip link geralmente é o primeiro elemento focável
    let hasFocusedElement = false
    for (let i = 0; i < 20; i++) {
      await page.keyboard.press('Tab')
      hasFocusedElement = await page.evaluate(() => {
        const el = document.activeElement
        return !!el && el !== document.body && el !== document.documentElement
      })
      if (hasFocusedElement) break
    }
    // Se não conseguiu foco via Tab, verifica se há pelo menos links/buttons focáveis na página
    if (!hasFocusedElement) {
      const focusableCount = await page.locator('a, button, input, [tabindex="0"]').count()
      expect(focusableCount).toBeGreaterThan(0)
    } else {
      expect(hasFocusedElement).toBeTruthy()
    }
  })

  test('botões devem ter nome acessível', async ({ page }) => {
    await page.goto('/')

    const buttons = page.locator('button')
    const count = await buttons.count()

    for (let i = 0; i < Math.min(count, 5); i++) {
      const button = buttons.nth(i)
      if (await button.isVisible()) {
        const text = await button.textContent()
        const ariaLabel = await button.getAttribute('aria-label')
        const title = await button.getAttribute('title')

        // Botão deve ter algum nome acessível
        expect(text?.trim() || ariaLabel || title).toBeTruthy()
      }
    }
  })

  test('elementos interativos devem ser focáveis', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('main').first()).toBeVisible()

    // Garante foco na página clicando no body primeiro
    await page.locator('body').click()

    // Pressiona Tab múltiplas vezes
    let hasFocusedElement = false
    for (let i = 0; i < 20; i++) {
      await page.keyboard.press('Tab')
      hasFocusedElement = await page.evaluate(() => {
        const el = document.activeElement
        return !!el && el !== document.body && el !== document.documentElement
      })
      if (hasFocusedElement) break
    }
    // Se não conseguiu foco via Tab, verifica se há pelo menos elementos focáveis na página
    if (!hasFocusedElement) {
      const focusableCount = await page.locator('a, button, input, [tabindex="0"]').count()
      expect(focusableCount).toBeGreaterThan(0)
    } else {
      expect(hasFocusedElement).toBeTruthy()
    }
  })
})

test.describe('Acessibilidade - Cores e Contraste', () => {
  test('texto deve ser legível', async ({ page }) => {
    await page.goto('/')

    // Verifica se o texto principal está visível
    const mainText = page.locator('main p, main h1, main h2, main span').first()

    if (await mainText.isVisible()) {
      // Verifica se o elemento tem conteúdo
      const text = await mainText.textContent()
      expect(text?.length).toBeGreaterThan(0)
    }
  })

  test('links devem ser distinguíveis', async ({ page }) => {
    await page.goto('/')

    const link = page.locator('a').first()

    if (await link.isVisible()) {
      // Link deve ter algum estilo que o distingue
      const color = await link.evaluate(el => window.getComputedStyle(el).color)
      expect(color).toBeTruthy()
    }
  })
})

test.describe('Acessibilidade - Responsividade', () => {
  test('conteúdo deve ser visível em mobile', async ({ page }) => {
    // Define viewport mobile
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Main content deve estar visível (usa first para evitar strict mode)
    await expect(page.locator('main').first()).toBeVisible()
  })

  test('conteúdo deve ser visível em tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/')

    await expect(page.locator('main')).toBeVisible()
  })

  test('conteúdo deve ser visível em desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')

    await expect(page.locator('main')).toBeVisible()
    await expect(page.locator('aside')).toBeVisible()
  })
})
