// @ts-check
import { test, expect } from '@playwright/test'
import {
  registerTestUser,
  loginViaAPI,
  createApiKey,
  setDashboardApiKey,
  createAuthenticatedUser,
} from '../helpers/auth.js'

/**
 * NOTA: el dashboard usa API Key (no email/password) como mecanismo de login.
 * El flow real:
 *   1. Usuario se registra via /api/v2/auth/register/ (email + password)
 *   2. Usuario hace login via /api/v2/auth/login/ (JWT)
 *   3. Usuario crea una API key via /api/v2/auth/api-keys/create/
 *   4. La API key se guarda en localStorage y es lo que el dashboard valida
 *
 * Los tests de este archivo reflejan ese flow real.
 */

test.describe('Authentication flows', () => {
  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.locator('form')).toBeVisible()
  })

  test('login page shows API key input', async ({ page }) => {
    await page.goto('/login')

    // El input es type=password (para la API key)
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('form button[type="submit"]')).toBeVisible()
  })

  test('registration API accepts valid payload', async ({ request }) => {
    const user = await registerTestUser(request)
    expect(user.email).toContain('@xcapit.test')
    expect(user.password).toBeTruthy()
  })

  test('login API returns JWT tokens', async ({ request }) => {
    const user = await registerTestUser(request)
    const token = await loginViaAPI(request, user.email, user.password)

    expect(token).toBeTruthy()
    expect(token.split('.').length).toBe(3) // JWT has 3 parts separated by dots
  })

  test('API key creation works with JWT', async ({ request }) => {
    const user = await registerTestUser(request)
    const jwt = await loginViaAPI(request, user.email, user.password)
    const apiKey = await createApiKey(request, jwt, 'test-auth-spec')

    expect(apiKey).toBeTruthy()
    expect(apiKey.length).toBeGreaterThan(20)
  })

  test('dashboard rejects access without API key', async ({ page }) => {
    await page.goto('/login')
    await page.evaluate(() => localStorage.clear())

    await page.goto('/dashboard')
    // Should redirect back to login or root
    await expect(page).toHaveURL(/\/(login|$)/, { timeout: 5_000 })
  })

  test('authenticated user can access dashboard', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/dashboard')

    // Should NOT redirect to login
    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('invalid API key via form shows error', async ({ page }) => {
    await page.goto('/login')

    const passwordInput = page.locator('input[type="password"]').first()
    await passwordInput.fill('invalid-api-key-12345')

    const submitButton = page.locator('form button[type="submit"]').first()
    await submitButton.click()

    // Error message should appear. The Login component renders errors inside
    // a div with class "bg-red-50 border border-red-200".
    const errorBox = page.locator('.bg-red-50').first()
    await expect(errorBox).toBeVisible({ timeout: 10_000 })
  })

  test('public register page loads', async ({ page }) => {
    await page.goto('/register')
    await expect(page).toHaveURL(/\/register/)
    await expect(page.locator('form')).toBeVisible()
  })
})
