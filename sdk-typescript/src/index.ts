/**
 * Xcapit FHE-ML SDK
 *
 * TypeScript SDK for the Xcapit Privacy-Preserving Machine Learning Platform.
 *
 * @packageDocumentation
 */

// Client
export { XcapitClient, XcapitSDKError } from './client';
export { default } from './client';

// Types - Enums
export {
  ModelType,
  ModelStatus,
  ConsortiumStatus,
  MemberStatus,
  ProposalType,
  ProposalStatus,
  ComplianceFramework,
} from './types';

// Types - API
export type {
  ApiResponse,
  ApiError,
  ResponseMeta,
  PaginationParams,
} from './types';

// Types - Models
export type {
  Model,
  ModelMetadata,
  CreateModelRequest,
  TrainModelRequest,
  TrainingResult,
  TrainingMetrics,
} from './types';

// Types - Predictions
export type {
  PredictionRequest,
  PredictionResponse,
  BatchPredictionRequest,
  BatchPredictionResponse,
} from './types';

// Types - Encryption
export type {
  EncryptionContext,
  EncryptedData,
  EncryptRequest,
  DecryptRequest,
} from './types';

// Types - Consortium
export type {
  Consortium,
  CreateConsortiumRequest,
  ConsortiumMember,
  Contribution,
  RecordContributionRequest,
} from './types';

// Types - Governance
export type {
  Proposal,
  CreateProposalRequest,
  VoteRequest,
  AuditEvent,
} from './types';

// Types - Compliance
export type {
  ComplianceReport,
  ComplianceFinding,
  GenerateReportRequest,
} from './types';

// Types - Data Quality
export type {
  DataQualityReport,
  DataQualityDimensions,
  DataQualityIssue,
} from './types';

// Types - Explainability
export type {
  ExplanationRequest,
  Explanation,
  FeatureImportance,
} from './types';

// Types - Blockchain
export type {
  BlockchainTransaction,
  ModelRegistryEntry,
  ComputationProof,
} from './types';

// Types - Configuration
export type {
  SDKConfig,
  BlockchainConfig,
  EncryptionConfig,
} from './types';

/**
 * Create a new XcapitClient instance
 *
 * @param config - SDK configuration
 * @returns XcapitClient instance
 *
 * @example
 * ```typescript
 * import { createClient, ModelType } from '@xcapit/fhe-ml-sdk';
 *
 * const client = createClient({
 *   apiUrl: 'https://api.xcapit.io',
 *   apiKey: process.env.XCAPIT_API_KEY,
 * });
 *
 * // Create a model
 * const model = await client.models.create({
 *   name: 'Credit Scoring Model',
 *   type: ModelType.LogisticRegression,
 * });
 *
 * // Train the model with encrypted data
 * const result = await client.models.train({
 *   modelId: model.id,
 *   encryptedData: myEncryptedTrainingData,
 *   epochs: 100,
 * });
 *
 * // Make predictions
 * const prediction = await client.predictions.predict({
 *   modelId: model.id,
 *   encryptedInput: encryptedFeatures,
 * });
 *
 * console.log('Prediction:', prediction.result);
 * ```
 */
export function createClient(config: import('./types').SDKConfig): import('./client').XcapitClient {
  const { XcapitClient } = require('./client');
  return new XcapitClient(config);
}

/**
 * SDK Version
 */
export const VERSION = '1.0.0';
