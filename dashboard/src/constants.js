/**
 * Xcapit FHE-ML Platform — shared constants
 */

export const COLORS = {
  primary: '#4f46e5',
  primaryDark: '#3730a3',
  primaryLight: '#eef2ff',
  secondary: '#7c3aed',
  success: '#059669',
  successLight: '#ecfdf5',
  warning: '#d97706',
  warningLight: '#fffbeb',
  danger: '#dc2626',
  dangerLight: '#fef2f2',
  info: '#0284c7',
  infoLight: '#f0f9ff',
  bg: '#f8fafc',
  card: '#ffffff',
  border: '#e2e8f0',
  text: '#1e293b',
  textSecondary: '#64748b',
  textMuted: '#94a3b8',
}

export const GRADIENTS = {
  primary: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
  success: 'linear-gradient(135deg, #059669, #10b981)',
  dark: 'linear-gradient(135deg, #1e293b, #334155)',
}

export const TIERS = {
  sandbox: { label: 'Sandbox', color: '#94a3b8', limit: '100 registros' },
  starter: { label: 'Starter', color: '#4f46e5', limit: '10K registros' },
  professional: { label: 'Professional', color: '#7c3aed', limit: '1M registros' },
  enterprise: { label: 'Enterprise', color: '#059669', limit: 'Ilimitado' },
}

export const STATUS_COLORS = {
  active: 'success',
  completed: 'success',
  pending: 'warning',
  training: 'primary',
  failed: 'danger',
  inactive: 'danger',
  draft: 'warning',
}

export const CRYPTO_LAYERS = [
  { key: 'fhe', label: 'FHE', full: 'Fully Homomorphic Encryption', icon: '🔐' },
  { key: 'zkp', label: 'ZKP', full: 'Zero-Knowledge Proofs', icon: '✓' },
  { key: 'mpc', label: 'MPC', full: 'Multi-Party Computation', icon: '🤝' },
  { key: 'dp', label: 'DP', full: 'Differential Privacy', icon: '📊' },
]

export const API_VERSION = 'v2'
export const APP_NAME = 'Xcapit FHE-ML'
export const APP_VERSION = '1.0.0-rc1'
