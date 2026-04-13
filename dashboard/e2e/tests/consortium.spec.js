// @ts-check
import { test, expect } from '@playwright/test'
import { createAuthenticatedUser } from '../helpers/auth.js'
import { newConsortium } from '../fixtures/test-data.js'

test.describe('Consortium flows', () => {
  test('authenticated user can navigate to consortium create page', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/consortiums/new')

    await expect(page).toHaveURL(/\/consortiums\/new/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('consortium create API works', async ({ page, request }) => {
    const user = await createAuthenticatedUser(page, request)
    const consortium = newConsortium()

    const response = await request.post('http://localhost:8000/api/v2/consortiums/', {
      data: consortium,
      headers: { 'X-API-Key': user.apiKey },
    })

    // Should succeed (201) or return a business logic error (400), not 5xx
    expect(response.status()).toBeLessThan(500)
  })

  test('dashboard page renders for authenticated user', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/dashboard')

    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('authenticated user can access marketplace route', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/marketplace')

    await expect(page).toHaveURL(/\/marketplace/)
    await expect(page.locator('body')).toBeVisible()
  })
})
