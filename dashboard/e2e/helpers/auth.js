/**
 * Auth helper for E2E tests.
 *
 * The Xcapit dashboard authenticates via API Key stored in localStorage
 * (key: 'xcapit_api_key'). The actual auth flow is:
 *
 *   1. Register a user       → POST /api/v2/auth/register/
 *   2. Login (get JWT token) → POST /api/v2/auth/login/
 *   3. Create API key        → POST /api/v2/auth/api-keys/create/ (Bearer JWT)
 *   4. Store key             → localStorage.setItem('xcapit_api_key', key)
 *   5. Navigate to dashboard → isAuthenticated() returns true
 *
 * Helpers here abstract that for tests.
 */

const BACKEND_URL = process.env.E2E_BACKEND_URL || 'http://localhost:8000'

/**
 * Registra un usuario nuevo via API y devuelve sus credenciales.
 * No loguea — usar junto con loginViaAPI + createApiKey para auth completa.
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
      first_name: 'E2E',
      last_name: 'Tester',
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
 * Login programatico via API. Devuelve el JWT access token.
 * Para el dashboard, usar createApiKey() despues.
 */
export async function loginViaAPI(request, email, password) {
  const response = await request.post(`${BACKEND_URL}/api/v2/auth/login/`, {
    data: { email, password },
  })

  if (!response.ok()) {
    const body = await response.text()
    throw new Error(`loginViaAPI failed: ${response.status()} ${body}`)
  }

  const data = await response.json()
  // Backend returns: {"tokens": {"access": "...", "refresh": "..."}, ...}
  const token = data.tokens?.access || data.access || data.token

  if (!token) {
    throw new Error('loginViaAPI: no access token in response')
  }

  return token
}

/**
 * Crea una API key usando un JWT access token.
 * Devuelve la key en texto plano (solo se muestra una vez por el backend).
 */
export async function createApiKey(request, jwtToken, name = 'e2e-test') {
  const response = await request.post(
    `${BACKEND_URL}/api/v2/auth/api-keys/create/`,
    {
      data: { name: `${name}-${Date.now()}` },
      headers: { Authorization: `Bearer ${jwtToken}` },
    },
  )

  if (!response.ok()) {
    const body = await response.text()
    throw new Error(`createApiKey failed: ${response.status()} ${body}`)
  }

  const data = await response.json()
  const key = data.api_key?.key || data.key

  if (!key) {
    throw new Error('createApiKey: no key in response')
  }

  return key
}

/**
 * Setea la API key en localStorage del browser para que el dashboard la use.
 * Requiere haber navegado a alguna pagina del dashboard primero.
 */
export async function setDashboardApiKey(page, apiKey) {
  // Necesitamos navegar a una pagina del dashboard antes de tocar localStorage
  await page.goto('/login')
  await page.evaluate((key) => {
    localStorage.setItem('xcapit_api_key', key)
  }, apiKey)
}

/**
 * Helper completo: registra usuario, crea API key, setea en localStorage.
 * Despues de esto, el usuario esta listo para navegar a rutas protegidas.
 *
 * @returns {Promise<{email, password, apiKey}>} credenciales completas
 */
export async function createAuthenticatedUser(page, request) {
  const user = await registerTestUser(request)
  const jwt = await loginViaAPI(request, user.email, user.password)
  const apiKey = await createApiKey(request, jwt)
  await setDashboardApiKey(page, apiKey)
  return { ...user, apiKey }
}
