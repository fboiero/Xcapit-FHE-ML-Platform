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

    // Should list at least 3 of the 4 tiers
    const tierTexts = ['free', 'starter', 'professional', 'enterprise']
    let visibleCount = 0

    for (const tier of tierTexts) {
      const count = await page.locator(`text=/${tier}/i`).count()
      if (count > 0) visibleCount++
    }

    expect(visibleCount).toBeGreaterThanOrEqual(3)
  })

  test('settings page is accessible', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/settings')

    await expect(page).toHaveURL(/\/settings/)
    await expect(page.locator('body')).toBeVisible()
  })
})
