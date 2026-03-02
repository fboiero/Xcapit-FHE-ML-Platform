/**
 * API Client for Xcapit Privacy Platform
 */

// Use environment variable for API base URL (set in .env or Vercel)
// In development, Vite proxy handles /api requests to localhost:8000
const API_BASE = import.meta.env.VITE_API_URL || '/api/v2/consortiums';

import { DEMO_API_KEY } from '../config/demo';
export { DEMO_API_KEY };

// Get stored API key
const getApiKey = () => localStorage.getItem('xcapit_api_key');

// Set API key
export const setApiKey = (key) => localStorage.setItem('xcapit_api_key', key);

// Clear API key (logout)
export const clearApiKey = () => {
  localStorage.removeItem('xcapit_api_key');
  localStorage.removeItem('xcapit_demo_scenario');
};

// Check if logged in
export const isAuthenticated = () => !!getApiKey();

// Check if in demo mode
export const isDemoMode = () => getApiKey() === DEMO_API_KEY;

// Fetch with retry logic for network errors and 5xx responses
const fetchWithRetry = async (url, options = {}, retries = 3) => {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 30000)

  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await fetch(url, { ...options, signal: controller.signal })
      clearTimeout(timeout)
      if (response.status >= 500 && attempt < retries - 1) {
        await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)))
        continue
      }
      return response
    } catch (err) {
      clearTimeout(timeout)
      if (attempt < retries - 1 && err.name !== 'AbortError') {
        await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)))
        continue
      }
      throw err
    }
  }
}

// Base fetch with auth
const apiFetch = async (endpoint, options = {}) => {
  const apiKey = getApiKey();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (apiKey) {
    headers['Authorization'] = `ApiKey ${apiKey}`;
  }

  const response = await fetchWithRetry(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(error.detail || `Error ${response.status}`);
  }

  return response.json();
};

// ============ Company API ============

export const registerCompany = async (name, email) => {
  const data = await apiFetch('/companies', {
    method: 'POST',
    body: JSON.stringify({ name, email }),
  });

  // Auto-login after registration
  if (data.api_key) {
    setApiKey(data.api_key);
  }

  return data;
};

export const getCurrentCompany = async () => {
  return apiFetch('/companies/me');
};

// ============ Consortium API ============

export const createConsortium = async (name, description, modelType, mlConfig = {}) => {
  return apiFetch('', {
    method: 'POST',
    body: JSON.stringify({
      name,
      description,
      model_type: modelType,
      ml_config: mlConfig,
    }),
  });
};

export const listConsortiums = async (status = null) => {
  const params = status ? `?status=${status}` : '';
  return apiFetch(`${params}`);
};

export const getConsortium = async (consortiumId) => {
  return apiFetch(`/${consortiumId}`);
};

export const getConsortiumStats = async (consortiumId) => {
  return apiFetch(`/${consortiumId}/stats`);
};

export const activateConsortium = async (consortiumId) => {
  return apiFetch(`/${consortiumId}/activate`, {
    method: 'POST',
  });
};

// ============ Invitation API ============

export const inviteToConsortium = async (consortiumId, email, role = 'contributor') => {
  return apiFetch(`/${consortiumId}/invite`, {
    method: 'POST',
    body: JSON.stringify({ email, role }),
  });
};

export const listInvitations = async (consortiumId) => {
  return apiFetch(`/${consortiumId}/invitations`);
};

export const acceptInvitation = async (inviteCode) => {
  return apiFetch('/join', {
    method: 'POST',
    body: JSON.stringify({ invite_code: inviteCode }),
  });
};

// ============ Members API ============

export const listMembers = async (consortiumId) => {
  return apiFetch(`/${consortiumId}/members`);
};

// ============ Data Upload API ============

export const uploadEncryptedData = async (consortiumId, file, metadata = {}) => {
  const apiKey = getApiKey();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('metadata', JSON.stringify(metadata));

  const response = await fetchWithRetry(`${API_BASE}/${consortiumId}/data`, {
    method: 'POST',
    headers: {
      'Authorization': `ApiKey ${apiKey}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error uploading data' }));
    throw new Error(error.detail);
  }

  return response.json();
};

// ============ Training API ============

export const startTraining = async (consortiumId) => {
  return apiFetch(`/${consortiumId}/train`, {
    method: 'POST',
  });
};

export const getTrainingStatus = async (consortiumId) => {
  return apiFetch(`/${consortiumId}/training-status`);
};

// ============ Results API ============

export const downloadResults = async (consortiumId) => {
  const apiKey = getApiKey();

  const response = await fetchWithRetry(`${API_BASE}/${consortiumId}/results`, {
    headers: {
      'Authorization': `ApiKey ${apiKey}`,
    },
  });

  if (!response.ok) {
    throw new Error('Error downloading results');
  }

  return response.blob();
};
