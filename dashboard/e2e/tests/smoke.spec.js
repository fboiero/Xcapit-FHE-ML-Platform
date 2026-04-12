// @ts-check
import { test, expect } from '@playwright/test'

/**
 * Smoke tests — la primera linea de defensa.
 *
 * Si estos fallan, el stack basico esta roto y no tiene sentido correr
 * el resto del suite. Correr PRIMERO en CI, con fail-fast.
 */

test.describe('Smoke: the stack is up', () => {
  test('dashboard serves HTML on port 5173', async ({ page }) => {
    const response = await page.goto('/')
    expect(response?.status()).toBeLessThan(500)
  })

  test('backend health endpoint responds', async ({ request }) => {
    const backendUrl = process.env.E2E_BACKEND_URL || 'http://localhost:8000'
    const response = await request.get(`${backendUrl}/health/`)
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    // Health endpoint should return a status field
    expect(data).toHaveProperty('status')
  })

  test('backend readiness endpoint responds', async ({ request }) => {
    const backendUrl = process.env.E2E_BACKEND_URL || 'http://localhost:8000'
    const response = await request.get(`${backendUrl}/health/ready/`)
    // Could be 200 (ready) or 503 (services not ready yet) — but never 5xx error
    expect([200, 503]).toContain(response.status())
  })

  test('public pages render without 500s', async ({ page }) => {
    const publicPaths = ['/login', '/register', '/pricing', '/sandbox-demo']

    for (const path of publicPaths) {
      const response = await page.goto(path)
      expect(response?.status(), `${path} should not 5xx`).toBeLessThan(500)
    }
  })
})
