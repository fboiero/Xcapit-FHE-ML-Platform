/**
 * Type definitions for Xcapit FHE-ML SDK
 */

// ============ Enums ============

export enum ModelType {
  LinearRegression = 'linear_regression',
  LogisticRegression = 'logistic_regression',
  DecisionTree = 'decision_tree',
  KMeans = 'kmeans',
  Ensemble = 'ensemble',
}

export enum ModelStatus {
  Draft = 'draft',
  Training = 'training',
  Ready = 'ready',
  Deployed = 'deployed',
  Archived = 'archived',
}

export enum ConsortiumStatus {
  Active = 'active',
  Paused = 'paused',
  Completed = 'completed',
  Dissolved = 'dissolved',
}

export enum MemberStatus {
  Pending = 'pending',
  Active = 'active',
  Suspended = 'suspended',
  Removed = 'removed',
}

export enum ProposalType {
  AddMember = 'add_member',
  RemoveMember = 'remove_member',
  ChangeModel = 'change_model',
  StartTraining = 'start_training',
  DistributeRewards = 'distribute_rewards',
  UpdateConfig = 'update_config',
  Dissolve = 'dissolve',
}

export enum ProposalStatus {
  Active = 'active',
  Passed = 'passed',
  Rejected = 'rejected',
  Executed = 'executed',
  Cancelled = 'cancelled',
}

export enum ComplianceFramework {
  GDPR = 'gdpr',
  HIPAA = 'hipaa',
  SOC2 = 'soc2',
  PCIDSS = 'pci_dss',
  LGPD = 'lgpd',
}

// ============ API Response Types ============

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: ResponseMeta;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ResponseMeta {
  page?: number;
  limit?: number;
  total?: number;
  hasMore?: boolean;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// ============ Model Types ============

export interface Model {
  id: string;
  name: string;
  type: ModelType;
  status: ModelStatus;
  version: string;
  owner: string;
  weightsHash?: string;
  accuracy?: number;
  createdAt: Date;
  updatedAt: Date;
  metadata?: ModelMetadata;
}

export interface ModelMetadata {
  description?: string;
  tags?: string[];
  framework?: string;
  inputShape?: number[];
  outputShape?: number[];
  hyperparameters?: Record<string, unknown>;
}

export interface CreateModelRequest {
  name: string;
  type: ModelType;
  version?: string;
  metadata?: ModelMetadata;
}

export interface TrainModelRequest {
  modelId: string;
  datasetId?: string;
  encryptedData?: string;
  hyperparameters?: Record<string, unknown>;
  epochs?: number;
  batchSize?: number;
}

export interface TrainingResult {
  modelId: string;
  accuracy: number;
  loss: number;
  epochs: number;
  trainingTime: number;
  weightsHash: string;
  metrics: TrainingMetrics;
}

export interface TrainingMetrics {
  trainAccuracy: number[];
  valAccuracy: number[];
  trainLoss: number[];
  valLoss: number[];
}

// ============ Prediction Types ============

export interface PredictionRequest {
  modelId: string;
  encryptedInput: string;
  returnEncrypted?: boolean;
}

export interface PredictionResponse {
  predictionId: string;
  modelId: string;
  result: number[] | string;
  encryptedResult?: string;
  confidence?: number;
  latencyMs: number;
  proofHash?: string;
}

export interface BatchPredictionRequest {
  modelId: string;
  encryptedInputs: string[];
  returnEncrypted?: boolean;
}

export interface BatchPredictionResponse {
  batchId: string;
  modelId: string;
  results: PredictionResponse[];
  totalLatencyMs: number;
}

// ============ Encryption Types ============

export interface EncryptionContext {
  contextId: string;
  publicKey: string;
  relinKeys?: string;
  galoisKeys?: string;
  scheme: 'ckks' | 'bfv';
  polyModulusDegree: number;
  scale: number;
}

export interface EncryptedData {
  ciphertext: string;
  shape: number[];
  contextId: string;
  createdAt: Date;
}

export interface EncryptRequest {
  data: number[];
  contextId?: string;
}

export interface DecryptRequest {
  ciphertext: string;
  contextId: string;
  secretKey: string;
}

// ============ Consortium Types ============

export interface Consortium {
  id: string;
  name: string;
  owner: string;
  status: ConsortiumStatus;
  memberCount: number;
  totalContributions: number;
  minVotingQuorum: number;
  votingDuration: number;
  modelConfigHash?: string;
  createdAt: Date;
}

export interface CreateConsortiumRequest {
  name: string;
  minVotingQuorum: number;
  votingDuration: number;
  modelType?: ModelType;
}

export interface ConsortiumMember {
  address: string;
  status: MemberStatus;
  joinedAt: Date;
  contributionCount: number;
  contributionWeight: number;
  lastContributionAt?: Date;
}

export interface Contribution {
  id: string;
  consortiumId: string;
  contributor: string;
  recordCount: number;
  featureCount: number;
  dataHash: string;
  checksumHash: string;
  timestamp: Date;
  verified: boolean;
}

export interface RecordContributionRequest {
  consortiumId: string;
  recordCount: number;
  featureCount: number;
  encryptedData: string;
}

// ============ Governance Types ============

export interface Proposal {
  id: string;
  consortiumId: string;
  type: ProposalType;
  proposer: string;
  status: ProposalStatus;
  data: string;
  createdAt: Date;
  expiresAt: Date;
  yesVotes: number;
  noVotes: number;
  executed: boolean;
}

export interface CreateProposalRequest {
  consortiumId: string;
  type: ProposalType;
  data: string;
  description?: string;
}

export interface VoteRequest {
  proposalId: string;
  support: boolean;
}

export interface AuditEvent {
  id: string;
  consortiumId: string;
  eventType: string;
  actor: string;
  targetId?: string;
  data?: string;
  timestamp: Date;
  previousEventHash: string;
}

// ============ Compliance Types ============

export interface ComplianceReport {
  id: string;
  framework: ComplianceFramework;
  status: 'compliant' | 'non_compliant' | 'pending';
  score: number;
  findings: ComplianceFinding[];
  generatedAt: Date;
  validUntil: Date;
}

export interface ComplianceFinding {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  description: string;
  recommendation: string;
  status: 'open' | 'resolved' | 'accepted';
}

export interface GenerateReportRequest {
  framework: ComplianceFramework;
  modelIds?: string[];
  consortiumIds?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
}

// ============ Data Quality Types ============

export interface DataQualityReport {
  datasetId: string;
  overallScore: number;
  dimensions: DataQualityDimensions;
  issues: DataQualityIssue[];
  generatedAt: Date;
}

export interface DataQualityDimensions {
  completeness: number;
  accuracy: number;
  consistency: number;
  timeliness: number;
  uniqueness: number;
}

export interface DataQualityIssue {
  dimension: keyof DataQualityDimensions;
  severity: 'critical' | 'warning' | 'info';
  column?: string;
  description: string;
  affectedRows: number;
}

// ============ Explainability Types ============

export interface ExplanationRequest {
  predictionId: string;
  method?: 'shap' | 'lime' | 'integrated_gradients';
  numFeatures?: number;
}

export interface Explanation {
  predictionId: string;
  method: string;
  featureImportances: FeatureImportance[];
  baseValue?: number;
  outputValue?: number;
  generatedAt: Date;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
  direction: 'positive' | 'negative';
  value?: number;
}

// ============ Blockchain Types ============

export interface BlockchainTransaction {
  txHash: string;
  blockNumber: number;
  from: string;
  to: string;
  status: 'pending' | 'confirmed' | 'failed';
  gasUsed?: number;
  timestamp: Date;
}

export interface ModelRegistryEntry {
  modelId: string;
  owner: string;
  modelType: string;
  version: string;
  weightsHash: string;
  verified: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface ComputationProof {
  computationId: string;
  modelId: string;
  inputHash: string;
  outputHash: string;
  proofHash: string;
  executor: string;
  timestamp: Date;
  verified: boolean;
}

// ============ SDK Configuration ============

export interface SDKConfig {
  apiUrl: string;
  apiKey?: string;
  timeout?: number;
  retries?: number;
  blockchain?: BlockchainConfig;
  encryption?: EncryptionConfig;
}

export interface BlockchainConfig {
  rpcUrl: string;
  chainId: number;
  privateKey?: string;
  contracts?: {
    modelRegistry?: string;
    computationVerifier?: string;
    consortiumGovernance?: string;
  };
}

export interface EncryptionConfig {
  polyModulusDegree?: number;
  coeffModBitSizes?: number[];
  scaleBits?: number;
  securityLevel?: 128 | 192 | 256;
}
