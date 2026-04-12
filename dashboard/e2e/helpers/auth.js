/**
 * Auth helper for E2E tests.
 *
 * Sirve para:
 * - Loguearse programaticamente (via API) para tests que ya validaron el login
 * - Registrar usuarios unicos por test (evitar colision entre runs paralelos)
 */

const BACKEND_URL = process.env.E2E_BACKEND_URL || 'http://localhost:8000'

/**
 * Registra un usuario nuevo via API y devuelve sus credenciales.
 * Uso: cuando un test necesita un usuario autenticado pero NO esta testeando el registro.
 */
export async function registerTestUser(request) {
  const unique = `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const email = `${unique}@xcapit.test`
  const password = 'E2ETestPass123!'

  const response = await request.post(`${BACKEND_URL}/api/v2/auth/register/`, {
    data: {
      email,
      password,
      password_confirm: password,
      company_name: `E2E Company ${unique}`,
    },
  })

  if (!response.ok()) {
    const body = await response.text()
    throw new Error(`registerTestUser failed: ${response.status()} ${body}`)
  }

  return { email, password }
}

/**
 * Login programatico via API. Setea el token en localStorage antes de navegar.
 * Mas rapido que llenar el form de login en cada test.
 */
export async function loginViaAPI(page, email, password) {
  const response = await page.request.post(`${BACKEND_URL}/api/v2/auth/login/`, {
    data: { email, password },
  })

  if (!response.ok()) {
    const body = await response.text()
    throw new Error(`loginViaAPI failed: ${response.status()} ${body}`)
  }

  const data = await response.json()
  const token = data.access || data.token

  if (!token) {
    throw new Error('loginViaAPI: no token in response')
  }

  // Setear el token en localStorage antes de cualquier navegacion.
  // Esto requiere cargar una pagina primero para tener acceso a window.localStorage.
  await page.goto('/login')
  await page.evaluate((t) => {
    localStorage.setItem('access_token', t)
  }, token)

  return token
}

/**
 * Helper combinado: registra + loguea. Para tests que solo necesitan "un usuario".
 */
export async function createAuthenticatedUser(page, request) {
  const user = await registerTestUser(request)
  await loginViaAPI(page, user.email, user.password)
  return user
}
