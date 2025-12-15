/**
 * Compliance API Client
 * Connects to the backend compliance endpoints (TIER 3)
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

// ============ Frameworks ============

export const listFrameworks = async () => {
  return apiFetch('/compliance/frameworks');
};

export const getFramework = async (frameworkId) => {
  return apiFetch(`/compliance/frameworks/${frameworkId}`);
};

export const enableFramework = async (consortiumId, frameworkId) => {
  return apiFetch('/compliance/frameworks/enable', {
    method: 'POST',
    body: JSON.stringify({
      consortium_id: consortiumId,
      framework_id: frameworkId,
    }),
  });
};

// ============ Settings ============

export const getComplianceSettings = async (consortiumId) => {
  return apiFetch(`/compliance/settings/${consortiumId}`);
};

// ============ Checks ============

export const getChecks = async (consortiumId, frameworkId = null, status = null) => {
  const params = new URLSearchParams();
  if (frameworkId) params.append('framework_id', frameworkId);
  if (status) params.append('check_status', status);

  const queryString = params.toString();
  return apiFetch(`/compliance/checks/${consortiumId}${queryString ? '?' + queryString : ''}`);
};

export const recordCheck = async (data) => {
  return apiFetch('/compliance/checks', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const runAutomatedChecks = async (consortiumId, frameworkId) => {
  return apiFetch('/compliance/checks/run', {
    method: 'POST',
    body: JSON.stringify({
      consortium_id: consortiumId,
      framework_id: frameworkId,
    }),
  });
};

// ============ Reports ============

export const generateReport = async (consortiumId, frameworkId) => {
  return apiFetch('/compliance/reports', {
    method: 'POST',
    body: JSON.stringify({
      consortium_id: consortiumId,
      framework_id: frameworkId,
    }),
  });
};

export const getReports = async (consortiumId, frameworkId = null) => {
  const params = frameworkId ? `?framework_id=${frameworkId}` : '';
  return apiFetch(`/compliance/reports/${consortiumId}${params}`);
};

// ============ Attestations ============

export const createAttestation = async (data) => {
  return apiFetch('/compliance/attestations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getAttestations = async (consortiumId, frameworkId = null, includeRevoked = false) => {
  const params = new URLSearchParams();
  if (frameworkId) params.append('framework_id', frameworkId);
  if (includeRevoked) params.append('include_revoked', 'true');

  const queryString = params.toString();
  return apiFetch(`/compliance/attestations/${consortiumId}${queryString ? '?' + queryString : ''}`);
};

// ============ Data Processing Records (GDPR) ============

export const recordDataProcessing = async (data) => {
  return apiFetch('/compliance/data-processing', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getDataProcessingRecords = async (consortiumId, companyId = null) => {
  const params = companyId ? `?company_id=${companyId}` : '';
  return apiFetch(`/compliance/data-processing/${consortiumId}${params}`);
};

// ============ Dashboard ============

export const getComplianceDashboard = async (consortiumId) => {
  return apiFetch(`/compliance/dashboard/${consortiumId}`);
};
