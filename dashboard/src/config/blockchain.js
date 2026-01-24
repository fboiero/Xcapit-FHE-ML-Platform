/**
 * Blockchain Configuration
 *
 * Contract addresses and network configuration for Xcapit FHE-ML Platform.
 * Supports both testnet (sandbox) and mainnet (production) environments.
 */

// =============================================================================
// Testnet (Sandbox) - Arbitrum Sepolia
// =============================================================================
// Use this for development, testing, and integration validation
// Deployed: 2026-01-24

export const TESTNET_CONFIG = {
  network: "arbitrum-sepolia",
  chainId: 421614,
  rpcUrl: "https://sepolia-rollup.arbitrum.io/rpc",
  explorer: "https://sepolia.arbiscan.io",
  contracts: {
    governance: "0xda52326d106A91A1F22A0c41Be2dc1F531C01F11",
    modelRegistry: "0x1296cCeF7803Bff51FB690afCFc586E7012417b8",
    computationVerifier: "0xa5f04E0aefe55173C91b949Aa2385f0228dd2921",
  },
  deployer: "0x1EFeA870E80aCa0E140A9C77d921FEd68F1D653D",
  deployedAt: "2026-01-24",
};

// =============================================================================
// Mainnet (Production) - Arbitrum One
// =============================================================================
// Use this for production with real customers
// Deployed: TBD (requires audit + multi-sig setup)

export const MAINNET_CONFIG = {
  network: "arbitrum-one",
  chainId: 42161,
  rpcUrl: import.meta.env.VITE_ARBITRUM_RPC_URL || "https://arb1.arbitrum.io/rpc",
  explorer: "https://arbiscan.io",
  contracts: {
    governance: import.meta.env.VITE_MAINNET_GOVERNANCE_ADDRESS || "",
    modelRegistry: import.meta.env.VITE_MAINNET_MODEL_REGISTRY_ADDRESS || "",
    computationVerifier: import.meta.env.VITE_MAINNET_COMPUTATION_VERIFIER_ADDRESS || "",
  },
  deployer: "",
  deployedAt: "",
};

// =============================================================================
// Environment Detection
// =============================================================================

/**
 * Get current blockchain environment from env var or default to testnet
 */
export const getBlockchainEnv = () => {
  return import.meta.env.VITE_BLOCKCHAIN_ENV || "testnet";
};

/**
 * Check if current environment is testnet
 */
export const isTestnet = () => {
  return getBlockchainEnv() === "testnet";
};

/**
 * Check if current environment is mainnet
 */
export const isMainnet = () => {
  return getBlockchainEnv() === "mainnet";
};

// =============================================================================
// Active Configuration
// =============================================================================

/**
 * Get active blockchain configuration based on environment
 */
export const getBlockchainConfig = () => {
  return isTestnet() ? TESTNET_CONFIG : MAINNET_CONFIG;
};

/**
 * Get contract addresses for active environment
 */
export const getContractAddresses = () => {
  return getBlockchainConfig().contracts;
};

/**
 * Get explorer URL for a contract or transaction
 */
export const getExplorerUrl = (addressOrTxHash, type = "address") => {
  const config = getBlockchainConfig();
  return `${config.explorer}/${type}/${addressOrTxHash}`;
};

// =============================================================================
// Default Export
// =============================================================================

const blockchainConfig = {
  testnet: TESTNET_CONFIG,
  mainnet: MAINNET_CONFIG,
  getConfig: getBlockchainConfig,
  getContracts: getContractAddresses,
  getExplorerUrl,
  isTestnet,
  isMainnet,
  env: getBlockchainEnv(),
};

export default blockchainConfig;
