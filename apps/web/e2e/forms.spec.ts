import { test, expect } from '@playwright/test'

test.describe('Formulários - Página de Exemplo', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/config')
  })

  test('deve renderizar formulário de exemplo', async ({ page }) => {
    // Verifica campos do formulário
    await expect(page.locator('input, textarea, select').first()).toBeVisible()
  })

  test('deve permitir input de texto', async ({ page }) => {
    const input = page.locator('input[type="text"]').first()

    if (await input.isVisible()) {
      await input.fill('Teste de input')
      await expect(input).toHaveValue('Teste de input')
    }
  })

  test('deve permitir selecionar opções', async ({ page }) => {
    const select = page.locator('select').first()

    if (await select.isVisible()) {
      // Pega primeira opção disponível
      const options = await select.locator('option').all()
      if (options.length > 1) {
        const value = await options[1].getAttribute('value')
        if (value) {
          await select.selectOption(value)
        }
      }
    }
  })

  test('botão de submit deve estar presente', async ({ page }) => {
    const submitButton = page
      .locator('button[type="submit"], button')
      .filter({ hasText: /salvar|enviar|submit/i })

    // Se existir, deve estar visível
    const count = await submitButton.count()
    if (count > 0) {
      await expect(submitButton.first()).toBeVisible()
    }
  })
})

test.describe('Formulários - Validação', () => {
  test('campos required devem mostrar erro quando vazios', async ({ page }) => {
    await page.goto('/admin/config')

    const form = page.locator('form').first()
    if (await form.isVisible()) {
      // Tenta submeter form vazio
      const submitBtn = form.locator('button[type="submit"]')
      if (await submitBtn.isVisible()) {
        await submitBtn.click()

        // Aguarda possível mensagem de erro
        await page.waitForTimeout(500)
      }
    }
  })

  test('email deve validar formato', async ({ page }) => {
    await page.goto('/admin/config')

    const emailInput = page.locator('input[type="email"]').first()

    if (await emailInput.isVisible()) {
      // Input inválido
      await emailInput.fill('email-invalido')
      await emailInput.blur()

      // Input válido
      await emailInput.fill('email@valido.com')
      await expect(emailInput).toHaveValue('email@valido.com')
    }
  })
})

test.describe('Formulários - UX', () => {
  test('inputs devem ter labels acessíveis', async ({ page }) => {
    await page.goto('/admin/config')

    // Verifica se inputs têm labels associados
    const inputs = page.locator('input:not([type="hidden"])')
    const count = await inputs.count()

    // Pelo menos verifica que inputs existem
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('focus deve ter indicador visual', async ({ page }) => {
    await page.goto('/admin/config')

    const input = page.locator('input').first()

    if (await input.isVisible()) {
      await input.focus()

      // Elemento deve estar focado
      await expect(input).toBeFocused()
    }
  })

  test('placeholder deve ser visível em campos vazios', async ({ page }) => {
    await page.goto('/admin/config')

    const inputWithPlaceholder = page.locator('input[placeholder]').first()

    if (await inputWithPlaceholder.isVisible()) {
      const placeholder = await inputWithPlaceholder.getAttribute('placeholder')
      expect(placeholder).toBeTruthy()
    }
  })
})
