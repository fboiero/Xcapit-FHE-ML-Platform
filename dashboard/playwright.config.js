// @ts-check
import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright configuration for the Xcapit dashboard E2E suite.
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e/tests',

  // Tiempo maximo por test: 60s (hay flows con FHE que pueden ser lentos)
  timeout: 60_000,

  // Tiempo para esperar por asserts (expect.poll)
  expect: {
    timeout: 10_000,
  },

  // Fail en CI si hay tests .only commiteados por error
  forbidOnly: !!process.env.CI,

  // Retries solo en CI (flakiness management)
  retries: process.env.CI ? 2 : 0,

  // Un worker en CI para evitar contention con el backend; paralelo en dev
  workers: process.env.CI ? 1 : undefined,

  // Reporter: list en local, html + github en CI
  reporter: process.env.CI
    ? [['list'], ['html', { open: 'never' }], ['github']]
    : [['list'], ['html', { open: 'on-failure' }]],

  // Opciones compartidas entre todos los tests
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',

    // Trace cuando falla un test (re-corrido via --trace retain-on-failure)
    trace: 'retain-on-failure',

    // Screenshots solo en fallas
    screenshot: 'only-on-failure',

    // Video solo en fallas
    video: 'retain-on-failure',

    // Ignorar HTTPS errors (desarrollo local)
    ignoreHTTPSErrors: true,

    // Viewport por defecto: desktop razonable
    viewport: { width: 1280, height: 720 },
  },

  // Proyectos: solo Chromium por default, Firefox/WebKit opt-in via CLI
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Descomentar para cross-browser testing (CI nightly):
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Levantar el dev server automaticamente si no esta corriendo
  // (en CI esperamos que lo levante el job, aqui es conveniencia local)
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: true,
        timeout: 120_000,
      },
})
