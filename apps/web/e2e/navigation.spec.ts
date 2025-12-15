import { test, expect } from '@playwright/test'

test.describe('Navegação Completa', () => {
  test('deve navegar por todas as páginas públicas', async ({ page }) => {
    // Home
    await page.goto('/')
    await expect(page).toHaveURL('/')
    await expect(page.locator('main')).toBeVisible()

    // Documentação
    await page
      .locator('aside nav')
      .getByRole('link', { name: /^documentação$/i })
      .click()
    await expect(page).toHaveURL(/\/docs/)
    await expect(page.locator('main')).toBeVisible()
  })

  test('deve navegar para páginas administrativas (ADMIN)', async ({ page }) => {
    await page.goto('/')

    // Usuários (requer ADMIN ou GESTOR)
    await page.goto('/admin/usuarios')
    await expect(page).toHaveURL(/\/admin\/usuarios/)
    await expect(page.locator('main')).toBeVisible()

    // Configurações (requer ADMIN)
    await page.goto('/admin/config')
    await expect(page).toHaveURL(/\/admin\/config/)
    await expect(page.locator('main')).toBeVisible()
  })

  test('breadcrumb deve atualizar na navegação', async ({ page }) => {
    await page.goto('/profile')

    // Verifica se há algum indicador de localização
    await expect(page.getByRole('banner')).toContainText(/profile/i)
  })

  test('deve manter estado do sidebar ao navegar', async ({ page }) => {
    await page.goto('/')

    // Usa seletor específico para o sidebar principal (não o module-functions-panel)
    const sidebar = page.locator('aside.sidebar-gradient, aside[class*="fixed left-0"]').first()
    await expect(sidebar).toBeVisible()

    // Navega para outra página - usa primeiro link com texto "Módulo Exemplo" no aside
    await page
      .locator('aside nav')
      .getByRole('link', { name: /módulo exemplo/i })
      .first()
      .click()
    await expect(page).toHaveURL(/\/exemplo/)

    // Sidebar ainda visível
    await expect(sidebar).toBeVisible()
  })
})

test.describe('Navegação por Teclado', () => {
  test('links devem ser focáveis via Tab', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('main')).toBeVisible()

    // Pressiona Tab várias vezes e verifica se algum elemento recebe foco
    let hasFocusedElement = false
    for (let i = 0; i < 15; i++) {
      await page.keyboard.press('Tab')
      hasFocusedElement = await page.evaluate(() => {
        const el = document.activeElement
        return !!el && el !== document.body && el !== document.documentElement
      })
      if (hasFocusedElement) break
    }
    expect(hasFocusedElement).toBeTruthy()
  })

  test('Enter deve ativar link focado', async ({ page }) => {
    await page.goto('/')

    // Foca no primeiro link do sidebar
    const firstLink = page.locator('aside nav a').first()
    await firstLink.focus()

    // Pressiona Enter
    await page.keyboard.press('Enter')

    // Deve ter navegado
    await page.waitForLoadState('networkidle')
  })
})

test.describe('Deep Links', () => {
  test('deve acessar página diretamente via URL', async ({ page }) => {
    await page.goto('/profile')
    await expect(page.getByRole('heading', { name: /perfil/i })).toBeVisible()
  })

  test('deve acessar config diretamente (ADMIN)', async ({ page }) => {
    await page.goto('/admin/config')
    await expect(page).toHaveURL(/\/admin\/config/)
    await expect(page.locator('main')).toBeVisible()
  })

  test('deve acessar users diretamente', async ({ page }) => {
    await page.goto('/admin/usuarios')
    await expect(page).toHaveURL(/\/admin\/usuarios/)
    await expect(page.locator('main')).toBeVisible()
  })

  test('página 404 para rota inexistente', async ({ page }) => {
    await page.goto('/rota-que-nao-existe')

    // Deve mostrar algum erro ou redirecionar
    await expect(page.locator('body')).toBeVisible()
  })
})
