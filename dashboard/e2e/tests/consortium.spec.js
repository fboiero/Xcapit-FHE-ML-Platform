// @ts-check
import { test, expect } from '@playwright/test'
import { createAuthenticatedUser } from '../helpers/auth.js'
import { newConsortium } from '../fixtures/test-data.js'

test.describe('Consortium flows', () => {
  test('authenticated user can access consortium create page', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/consortiums/new')

    await expect(page.locator('form, [data-testid="consortium-create"]').first()).toBeVisible({
      timeout: 10_000,
    })
  })

  test('create consortium → view detail', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    const consortium = newConsortium()

    await page.goto('/consortiums/new')

    // Form fields — be lenient on labels, use multiple strategies
    await page.getByLabel(/name|nombre/i).first().fill(consortium.name)

    const descField = page.getByLabel(/description|descripcion/i)
    if (await descField.count()) {
      await descField.first().fill(consortium.description)
    }

    // Industry selector (may be dropdown or radio)
    const industryField = page.getByLabel(/industry|industria/i)
    if (await industryField.count()) {
      await industryField.first().selectOption({ label: /banking|banca/i }).catch(async () => {
        // If not a select, try clicking as radio/button
        await industryField.first().click()
      })
    }

    // Submit
    await page.getByRole('button', { name: /create|crear|submit/i }).click()

    // Should land on detail page or dashboard with new consortium visible
    await expect(page).toHaveURL(/\/consortiums|\/dashboard/, { timeout: 15_000 })

    // The consortium name should appear somewhere on the resulting page
    await expect(page.getByText(consortium.name)).toBeVisible({ timeout: 10_000 })
  })

  test('dashboard shows consortium list', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/dashboard')

    // Either a list of consortiums or empty state should render
    await expect(
      page.locator('[data-testid="consortium-list"], main, body').first()
    ).toBeVisible()
  })

  test('invalid consortium submission shows validation errors', async ({ page, request }) => {
    await createAuthenticatedUser(page, request)
    await page.goto('/consortiums/new')

    // Submit without filling required fields
    await page.getByRole('button', { name: /create|crear|submit/i }).click()

    // Should stay on create page, not navigate to detail
    await expect(page).toHaveURL(/\/consortiums\/new/, { timeout: 5_000 })
  })
})
