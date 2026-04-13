// @ts-check
import { test, expect } from '@playwright/test'
import { createAuthenticatedUser } from '../helpers/auth.js'

test.describe('Trial / freemium flows', () => {
  test('authenticated user can access trial dashboard', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/trial')

    await expect(page).toHaveURL(/\/trial/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('billing page loads for authenticated user', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/billing')

    await expect(page).toHaveURL(/\/billing/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('pricing tier information is visible', async ({ page }) => {
    await page.goto('/pricing')

    // Dashboard uses Spanish tier names: Gratuito, Starter, Profesional, Enterprise
    // Also accept English names for i18n flexibility
    const tierPatterns = [
      /gratuito|free/i,
      /starter/i,
      /profesional|professional/i,
      /enterprise/i,
    ]

    let visibleCount = 0
    for (const pattern of tierPatterns) {
      const count = await page.locator('body').filter({ hasText: pattern }).count()
      if (count > 0) visibleCount++
    }

    expect(visibleCount, 'at least 3 of 4 tiers visible').toBeGreaterThanOrEqual(3)
  })

  test('settings page is accessible', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/settings')

    await expect(page).toHaveURL(/\/settings/)
    await expect(page.locator('body')).toBeVisible()
  })
})
