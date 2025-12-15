/**
 * Data Quality API Client
 * Connects to the backend data quality endpoints (TIER 3)
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const getApiKey = () => localStorage.getItem('xcapit_api_key');

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

// ============ Assessments ============

export const assessQuality = async (data) => {
  return apiFetch('/quality/assess', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getAssessments = async (consortiumId, companyId = null, limit = 50) => {
  const params = new URLSearchParams();
  if (companyId) params.append('company_id', companyId);
  if (limit) params.append('limit', limit);

  const queryString = params.toString();
  return apiFetch(`/quality/assessments/${consortiumId}${queryString ? '?' + queryString : ''}`);
};

export const getLatestAssessment = async (consortiumId, targetCompanyId = null) => {
  const params = targetCompanyId ? `?target_company_id=${targetCompanyId}` : '';
  return apiFetch(`/quality/assessments/${consortiumId}/latest${params}`);
};

// ============ History ============

export const getQualityHistory = async (consortiumId, metric = null, companyId = null, days = 30) => {
  const params = new URLSearchParams();
  if (metric) params.append('metric', metric);
  if (companyId) params.append('company_id', companyId);
  if (days) params.append('days', days);

  const queryString = params.toString();
  return apiFetch(`/quality/history/${consortiumId}${queryString ? '?' + queryString : ''}`);
};

// ============ Rules ============

export const setQualityRule = async (data) => {
  return apiFetch('/quality/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getQualityRules = async (consortiumId) => {
  return apiFetch(`/quality/rules/${consortiumId}`);
};

// ============ Alerts ============

export const getQualityAlerts = async (consortiumId, severity = null, status = null) => {
  const params = new URLSearchParams();
  if (severity) params.append('severity', severity);
  if (status) params.append('alert_status', status);

  const queryString = params.toString();
  return apiFetch(`/quality/alerts/${consortiumId}${queryString ? '?' + queryString : ''}`);
};

export const acknowledgeAlert = async (alertId, notes = null) => {
  return apiFetch(`/quality/alerts/${alertId}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  });
};

// ============ Dashboard ============

export const getQualityDashboard = async (consortiumId) => {
  return apiFetch(`/quality/dashboard/${consortiumId}`);
};
