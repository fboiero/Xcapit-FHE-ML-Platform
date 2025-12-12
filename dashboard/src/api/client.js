/**
 * API Client for Xcapit Privacy Platform
 */

// Use environment variable for API base URL (set in .env or Vercel)
// In development, Vite proxy handles /api requests to localhost:8000
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1/consortiums';

// Demo API Key - for sandbox demo mode
export const DEMO_API_KEY = 'demo_xcapit_2024_public_access';

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

// Base fetch with auth
const apiFetch = async (endpoint, options = {}) => {
  const apiKey = getApiKey();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
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

  const response = await fetch(`${API_BASE}/${consortiumId}/data`, {
    method: 'POST',
    headers: {
      'X-API-Key': apiKey,
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

  const response = await fetch(`${API_BASE}/${consortiumId}/results`, {
    headers: {
      'X-API-Key': apiKey,
    },
  });

  if (!response.ok) {
    throw new Error('Error downloading results');
  }

  return response.blob();
};
