/**
 * Governance API Client
 * Connects to the backend governance endpoints
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

// ============ Contributions ============
// Contributions live under the consortiums module

export const getContributions = async (consortiumId) => {
  return apiFetch(`/consortiums/${consortiumId}/contributions/`);
};

export const getContributionSummary = async (consortiumId) => {
  return apiFetch(`/consortiums/${consortiumId}/contributions/`);
};

export const recordContribution = async (data) => {
  const consortiumId = data.consortium_id || data.consortium;
  return apiFetch(`/consortiums/${consortiumId}/contributions/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

// ============ Proposals ============

export const getProposals = async (consortiumId, status = null) => {
  const params = new URLSearchParams({ consortium_id: consortiumId });
  if (status) params.append('status', status);
  return apiFetch(`/governance/proposals/?${params}`);
};

export const getProposal = async (consortiumId, proposalId) => {
  return apiFetch(`/governance/proposals/${proposalId}/`);
};

export const createProposal = async (data) => {
  return apiFetch('/governance/proposals/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const castVote = async (proposalId, support, comment = null) => {
  return apiFetch('/governance/votes/', {
    method: 'POST',
    body: JSON.stringify({
      proposal: proposalId,
      support,
      comment,
    }),
  });
};

export const executeProposal = async (proposalId) => {
  return apiFetch(`/governance/proposals/${proposalId}/execute/`, {
    method: 'POST',
  });
};

export const getProposalVotes = async (proposalId) => {
  return apiFetch(`/governance/proposals/${proposalId}/votes/`);
};

// ============ Audit Trail ============

export const getAuditTrail = async (consortiumId, eventType = null, limit = 100, offset = 0) => {
  const params = new URLSearchParams({ consortium_id: consortiumId });
  if (eventType) params.append('event_type', eventType);
  if (limit) params.append('limit', limit);
  if (offset) params.append('offset', offset);

  return apiFetch(`/governance/audit-events/?${params}`);
};

export const verifyAuditTrail = async (consortiumId) => {
  return apiFetch(`/governance/audit-events/verify/?consortium_id=${consortiumId}`);
};

// ============ Rewards ============

export const distributeRewards = async (consortiumId, amount) => {
  return apiFetch('/governance/rewards/distribute/', {
    method: 'POST',
    body: JSON.stringify({
      consortium_id: consortiumId,
      amount,
    }),
  });
};

export const getRewardHistory = async (consortiumId) => {
  return apiFetch(`/governance/rewards/?consortium_id=${consortiumId}`);
};
