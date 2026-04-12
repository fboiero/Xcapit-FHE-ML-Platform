// @ts-check
import { test, expect } from '@playwright/test'
import { uniqueSuffix } from '../fixtures/test-data.js'
import { registerTestUser, loginViaAPI } from '../helpers/auth.js'

test.describe('Authentication flows', () => {
  test('login page renders and redirects unauthenticated users', async ({ page }) => {
    await page.goto('/')
    // Unauthenticated users go to /login
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.locator('form')).toBeVisible()
  })

  test('login with valid credentials redirects to dashboard', async ({ page, request }) => {
    const user = await registerTestUser(request)
    await page.goto('/login')

    await page.getByLabel(/email/i).fill(user.email)
    await page.getByLabel(/password/i).fill(user.password)
    await page.getByRole('button', { name: /log in|iniciar/i }).click()

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15_000 })
  })

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill('nonexistent@xcapit.test')
    await page.getByLabel(/password/i).fill('wrong-password')
    await page.getByRole('button', { name: /log in|iniciar/i }).click()

    // Error message should appear — could be toast, inline, or banner
    await expect(
      page.locator(
        'text=/invalid|incorrecto|credentials|credenciales|error/i'
      )
    ).toBeVisible({ timeout: 10_000 })

    // Still on login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('register → pricing → trial flow', async ({ page }) => {
    const suffix = uniqueSuffix()
    const email = `register-${suffix}@xcapit.test`

    await page.goto('/register')

    await page.getByLabel(/email/i).fill(email)
    await page.getByLabel(/password/i).first().fill('E2ETestPass123!')

    // Some forms have password_confirm field
    const confirmField = page.getByLabel(/confirm|confirmar/i)
    if (await confirmField.count()) {
      await confirmField.fill('E2ETestPass123!')
    }

    // Company name field (required per backend serializer)
    const companyField = page.getByLabel(/company|empresa/i)
    if (await companyField.count()) {
      await companyField.fill(`E2E Corp ${suffix}`)
    }

    await page.getByRole('button', { name: /register|registr|sign up/i }).click()

    // After register, user typically lands on pricing or dashboard
    await expect(page).toHaveURL(/\/pricing|\/dashboard|\/trial/, { timeout: 15_000 })
  })

  test('protected route redirects unauthenticated to login', async ({ page }) => {
    // Clear any auth state
    await page.goto('/login')
    await page.evaluate(() => localStorage.clear())

    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/(login|$)/, { timeout: 5_000 })
  })

  test('authenticated user sees dashboard', async ({ page, request }) => {
    const user = await registerTestUser(request)
    await loginViaAPI(page, user.email, user.password)
    await page.goto('/dashboard')

    // Dashboard should render main content — be lenient on exact copy
    await expect(page.locator('body')).toBeVisible()
    // Either a navigation or dashboard-specific content should be present
    await expect(
      page.locator('nav, [role="navigation"], [data-testid="dashboard"]').first()
    ).toBeVisible({ timeout: 10_000 })
  })
})
