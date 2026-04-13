// @ts-check
import { test, expect } from '@playwright/test'
import { createAuthenticatedUser } from '../helpers/auth.js'

test.describe('Marketplace flows', () => {
  test('authenticated user can access marketplace', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/marketplace')

    await expect(page).toHaveURL(/\/marketplace/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('marketplace loads without page errors', async ({ page, request }) => {
    const consoleErrors = []
    page.on('pageerror', (err) => consoleErrors.push(err.message))

    await createAuthenticatedUser(page, request)
    await page.goto('/marketplace')
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {})

    expect(consoleErrors, 'no uncaught page errors').toEqual([])
  })

  test('model deployment page is reachable', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/deployment')

    await expect(page).toHaveURL(/\/deployment/)
    await expect(page.locator('body')).toBeVisible()
  })
})
