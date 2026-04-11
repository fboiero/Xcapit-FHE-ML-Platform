/**
 * Trial / Subscription API Client for Xcapit Privacy Platform
 *
 * Handles trial lifecycle, usage tracking, and plan upgrades.
 */

const SANDBOX_API_BASE =
  import.meta.env.VITE_API_URL?.replace('/api/v2/consortiums', '/api/v2/sandbox') ||
  '/api/v2/sandbox'

const getAuthHeaders = () => {
  const token = localStorage.getItem('xcapit_access_token')
  const apiKey = localStorage.getItem('xcapit_api_key')

  const headers = { 'Content-Type': 'application/json' }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  } else if (apiKey) {
    headers['Authorization'] = `ApiKey ${apiKey}`
  }

  return headers
}

const trialFetch = async (endpoint, options = {}) => {
  const response = await fetch(`${SANDBOX_API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    const err = new Error(error.detail || `Error ${response.status}`)
    err.error_code = error.error_code
    err.status = response.status
    throw err
  }

  return response.json()
}

// ============ Trial Lifecycle ============

/** Start a 14-day trial for the current company */
export const startTrial = () =>
  trialFetch('/trial/start/', { method: 'POST' })

/** Get current trial/subscription status + usage */
export const getTrialStatus = () =>
  trialFetch('/trial/status/')

/** Get detailed usage breakdown */
export const getTrialUsage = () =>
  trialFetch('/trial/usage/')

/**
 * Request upgrade to a paid tier
 * @param {'starter'|'professional'|'enterprise'} targetTier
 */
export const requestUpgrade = (targetTier) =>
  trialFetch('/trial/upgrade/', {
    method: 'POST',
    body: JSON.stringify({ target_tier: targetTier }),
  })

// ============ Data Upload ============

/**
 * Upload data to a consortium (enforces trial limits)
 * @param {string} consortiumId
 * @param {File} file
 */
export const uploadTrialData = async (consortiumId, file) => {
  const formData = new FormData()
  formData.append('consortium_id', consortiumId)
  formData.append('file', file)

  const headers = { ...getAuthHeaders() }
  delete headers['Content-Type'] // let browser set multipart boundary

  const response = await fetch(`${SANDBOX_API_BASE}/trial/upload-data/`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error subiendo datos' }))
    const err = new Error(error.detail || `Error ${response.status}`)
    err.error_code = error.error_code
    err.status = response.status
    throw err
  }

  return response.json()
}

// ============ Plans ============

/** Get plans comparison (public endpoint, no auth needed) */
export const getPlansComparison = async () => {
  const response = await fetch(`${SANDBOX_API_BASE}/plans/`, {
    headers: { 'Content-Type': 'application/json' },
  })

  if (!response.ok) {
    throw new Error('Error obteniendo planes')
  }

  return response.json()
}

// ============ Helpers ============

/** Format bytes to human readable */
export const formatBytes = (bytes) => {
  if (bytes === -1) return 'Ilimitado'
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

/** Format limit value (-1 = unlimited) */
export const formatLimit = (value) => {
  if (value === -1) return 'Ilimitado'
  return value.toLocaleString()
}
