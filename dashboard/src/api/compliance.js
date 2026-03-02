/**
 * Compliance API Client
 * Connects to the backend compliance endpoints (TIER 3)
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

// ============ Frameworks ============

export const listFrameworks = async () => {
  return apiFetch('/compliance/frameworks/');
};

export const getFramework = async (frameworkId) => {
  return apiFetch(`/compliance/frameworks/${frameworkId}/`);
};

export const enableFramework = async (consortiumId, frameworkId) => {
  return apiFetch('/compliance/settings/', {
    method: 'POST',
    body: JSON.stringify({
      consortium: consortiumId,
      enabled_frameworks: [frameworkId],
    }),
  });
};

// ============ Settings ============

export const getComplianceSettings = async (consortiumId) => {
  return apiFetch(`/compliance/settings/?consortium_id=${consortiumId}`);
};

// ============ Checks ============

export const getChecks = async (consortiumId, frameworkId = null, status = null) => {
  const params = new URLSearchParams({ consortium_id: consortiumId });
  if (frameworkId) params.append('framework_id', frameworkId);
  if (status) params.append('status', status);

  return apiFetch(`/compliance/checks/?${params}`);
};

export const recordCheck = async (data) => {
  return apiFetch('/compliance/checks/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const runAutomatedChecks = async (consortiumId, frameworkId) => {
  return apiFetch('/compliance/checks/run/', {
    method: 'POST',
    body: JSON.stringify({
      consortium_id: consortiumId,
      framework_id: frameworkId,
    }),
  });
};

// ============ Reports ============

export const generateReport = async (consortiumId, frameworkId) => {
  return apiFetch('/compliance/reports/generate/', {
    method: 'POST',
    body: JSON.stringify({
      consortium_id: consortiumId,
      framework_id: frameworkId,
    }),
  });
};

export const getReports = async (consortiumId, frameworkId = null) => {
  const params = new URLSearchParams({ consortium_id: consortiumId });
  if (frameworkId) params.append('framework_id', frameworkId);
  return apiFetch(`/compliance/reports/?${params}`);
};

// ============ Attestations ============

export const createAttestation = async (data) => {
  return apiFetch('/compliance/attestations/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getAttestations = async (consortiumId, frameworkId = null, includeRevoked = false) => {
  const params = new URLSearchParams({ consortium_id: consortiumId });
  if (frameworkId) params.append('framework_id', frameworkId);
  if (includeRevoked) params.append('include_revoked', 'true');

  return apiFetch(`/compliance/attestations/?${params}`);
};

// ============ Data Processing Records (GDPR) ============

export const recordDataProcessing = async (data) => {
  return apiFetch('/compliance/data-processing/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getDataProcessingRecords = async (consortiumId, companyId = null) => {
  const params = new URLSearchParams({ consortium_id: consortiumId });
  if (companyId) params.append('company_id', companyId);
  return apiFetch(`/compliance/data-processing/?${params}`);
};

// ============ Dashboard ============

export const getComplianceDashboard = async (consortiumId) => {
  return apiFetch(`/compliance/settings/?consortium_id=${consortiumId}`);
};
