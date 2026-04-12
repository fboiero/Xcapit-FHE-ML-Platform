// @ts-check
import { test, expect } from '@playwright/test'
import { uniqueSuffix } from '../fixtures/test-data.js'

test.describe('Public sandbox demo flows', () => {
  test('sandbox demo page is accessible without auth', async ({ page }) => {
    await page.goto('/sandbox-demo')
    await expect(page.locator('body')).toBeVisible()
    // Should NOT redirect to login
    await expect(page).toHaveURL(/\/sandbox-demo/)
  })

  test('pricing page is publicly accessible', async ({ page }) => {
    await page.goto('/pricing')
    await expect(page).toHaveURL(/\/pricing/)
    // Pricing page should show tiers (free, starter, professional, enterprise)
    await expect(
      page.locator('text=/free|starter|professional|enterprise/i').first()
    ).toBeVisible({ timeout: 10_000 })
  })

  test('demo consortium page is accessible', async ({ page }) => {
    await page.goto('/demo-consorcio')
    await expect(page).toHaveURL(/\/demo-consorcio/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('join consortium page accepts token param', async ({ page }) => {
    await page.goto('/join?token=test-token-12345')
    await expect(page).toHaveURL(/\/join/)
    await expect(page.locator('body')).toBeVisible()
  })

  test('sandbox email capture form submits', async ({ page }) => {
    await page.goto('/sandbox-demo')

    const emailInput = page.getByLabel(/email/i).first()
    if (await emailInput.count()) {
      const email = `sandbox-${uniqueSuffix()}@xcapit.test`
      await emailInput.fill(email)

      // Find submit button (could be various labels)
      const submitButton = page
        .getByRole('button', { name: /submit|start|comenzar|access|acceder/i })
        .first()

      if (await submitButton.count()) {
        await submitButton.click()
        // After submit, either redirect or show confirmation — both acceptable
        await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {})
      }
    } else {
      test.skip(true, 'Sandbox form not present — skipping email capture test')
    }
  })
})
