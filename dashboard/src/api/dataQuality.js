/**
 * Data Quality API Client
 * Connects to the backend data quality endpoints (TIER 3)
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api/v2';

const getApiKey = () => localStorage.getItem('xcapit_api_key');

const apiFetch = async (endpoint, options = {}) => {
  const apiKey = getApiKey();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (apiKey) {
    headers['Authorization'] = `ApiKey ${apiKey}`;
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

// ============ Assessments ============

export const assessQuality = async (data) => {
  return apiFetch('/data-quality/assessments/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getAssessments = async (consortiumId, companyId = null, limit = 50) => {
  const params = new URLSearchParams({ consortium: consortiumId });
  if (companyId) params.append('company', companyId);
  if (limit) params.append('limit', limit);

  return apiFetch(`/data-quality/assessments/?${params}`);
};

export const getLatestAssessment = async (consortiumId, targetCompanyId = null) => {
  const params = new URLSearchParams({ consortium: consortiumId });
  if (targetCompanyId) params.append('company', targetCompanyId);
  return apiFetch(`/data-quality/assessments/summary/?${params}`);
};

// ============ Rules ============

export const setQualityRule = async (data) => {
  return apiFetch('/data-quality/rules/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getQualityRules = async (consortiumId) => {
  return apiFetch(`/data-quality/rules/?consortium=${consortiumId}`);
};

// ============ Alerts ============

export const getQualityAlerts = async (consortiumId, severity = null, status = null) => {
  const params = new URLSearchParams({ consortium: consortiumId });
  if (severity) params.append('severity', severity);
  if (status) params.append('status', status);

  return apiFetch(`/data-quality/alerts/?${params}`);
};

export const acknowledgeAlert = async (alertId, notes = null) => {
  return apiFetch(`/data-quality/alerts/${alertId}/acknowledge/`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  });
};

// ============ Dashboard ============

export const getQualityDashboard = async (consortiumId) => {
  return apiFetch('/data-quality/dashboard/');
};
