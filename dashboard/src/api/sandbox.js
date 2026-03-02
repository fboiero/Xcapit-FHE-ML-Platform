/**
 * Sandbox API Client for Xcapit Privacy Platform
 *
 * Handles sandbox lead capture and token verification.
 */

// API base for sandbox endpoints
const SANDBOX_API_BASE = import.meta.env.VITE_API_URL?.replace('/api/v2/consortiums', '/api/v2/sandbox') || '/api/v2/sandbox';

// Storage keys
const SANDBOX_TOKEN_KEY = 'xcapit_sandbox_token';
const SANDBOX_EMAIL_KEY = 'xcapit_sandbox_email';
const SANDBOX_EXPIRES_KEY = 'xcapit_sandbox_expires';

/**
 * Request sandbox access with email
 * @param {string} email - User email
 * @param {object} tracking - Optional UTM tracking params
 * @returns {Promise<{token: string, email: string, expires_at: string}>}
 */
export const requestSandboxAccess = async (email, tracking = {}) => {
  const response = await fetch(`${SANDBOX_API_BASE}/leads/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      source: tracking.source || 'sandbox_demo',
      utm_campaign: tracking.utm_campaign || '',
      utm_source: tracking.utm_source || '',
      utm_medium: tracking.utm_medium || '',
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error requesting access' }));
    throw new Error(error.detail || error.email?.[0] || 'Invalid email');
  }

  const data = await response.json();

  // Store token and email
  localStorage.setItem(SANDBOX_TOKEN_KEY, data.token);
  localStorage.setItem(SANDBOX_EMAIL_KEY, data.email);
  localStorage.setItem(SANDBOX_EXPIRES_KEY, data.expires_at);

  return data;
};

/**
 * Verify sandbox token is still valid
 * @param {string} token - Sandbox token
 * @returns {Promise<{valid: boolean, email?: string, expires_at?: string}>}
 */
export const verifySandboxToken = async (token) => {
  const response = await fetch(`${SANDBOX_API_BASE}/leads/verify/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token }),
  });

  const data = await response.json();

  // Handle expired tokens
  if (response.status === 410) {
    clearSandboxAccess();
    return { valid: false, expired: true };
  }

  if (!response.ok) {
    return { valid: false };
  }

  return data;
};

/**
 * Get stored sandbox token
 * @returns {string|null}
 */
export const getSandboxToken = () => localStorage.getItem(SANDBOX_TOKEN_KEY);

/**
 * Get stored sandbox email
 * @returns {string|null}
 */
export const getSandboxEmail = () => localStorage.getItem(SANDBOX_EMAIL_KEY);

/**
 * Get stored sandbox expiry date
 * @returns {Date|null}
 */
export const getSandboxExpiry = () => {
  const expires = localStorage.getItem(SANDBOX_EXPIRES_KEY);
  return expires ? new Date(expires) : null;
};

/**
 * Check if user has sandbox access
 * @returns {boolean}
 */
export const hasSandboxAccess = () => {
  const token = getSandboxToken();
  const expires = getSandboxExpiry();

  if (!token || !expires) return false;

  // Check if expired locally
  return new Date() < expires;
};

/**
 * Clear sandbox access (logout)
 */
export const clearSandboxAccess = () => {
  localStorage.removeItem(SANDBOX_TOKEN_KEY);
  localStorage.removeItem(SANDBOX_EMAIL_KEY);
  localStorage.removeItem(SANDBOX_EXPIRES_KEY);
};

/**
 * Get time remaining in sandbox
 * @returns {{days: number, hours: number, minutes: number}|null}
 */
export const getSandboxTimeRemaining = () => {
  const expires = getSandboxExpiry();
  if (!expires) return null;

  const now = new Date();
  const diff = expires - now;

  if (diff <= 0) return null;

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  return { days, hours, minutes };
};

/**
 * Parse UTM parameters from URL
 * @returns {object}
 */
export const getUTMParams = () => {
  const params = new URLSearchParams(window.location.search);
  return {
    utm_campaign: params.get('utm_campaign') || '',
    utm_source: params.get('utm_source') || '',
    utm_medium: params.get('utm_medium') || '',
    source: params.get('ref') || 'direct',
  };
};
