/**
 * Xcapit FHE-ML SDK Client
 *
 * Main client for interacting with the Xcapit FHE-ML Platform API.
 */

import {
  ApiResponse,
  ApiError,
  SDKConfig,
  PaginationParams,
  ResponseMeta,
  Model,
  CreateModelRequest,
  TrainModelRequest,
  TrainingResult,
  PredictionRequest,
  PredictionResponse,
  BatchPredictionRequest,
  BatchPredictionResponse,
  EncryptionContext,
  EncryptedData,
  EncryptRequest,
  Consortium,
  CreateConsortiumRequest,
  ConsortiumMember,
  Contribution,
  RecordContributionRequest,
  Proposal,
  CreateProposalRequest,
  VoteRequest,
  AuditEvent,
  ComplianceReport,
  GenerateReportRequest,
  DataQualityReport,
  Explanation,
  ExplanationRequest,
} from './types';

/**
 * Custom error class for SDK errors
 */
export class XcapitSDKError extends Error {
  public code: string;
  public details?: Record<string, unknown>;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'XcapitSDKError';
    this.code = error.code;
    this.details = error.details;
  }
}

/**
 * HTTP client wrapper with retry logic
 */
class HttpClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private retries: number;

  constructor(config: SDKConfig) {
    this.baseUrl = config.apiUrl.replace(/\/$/, '');
    this.apiKey = config.apiKey;
    this.timeout = config.timeout ?? 30000;
    this.retries = config.retries ?? 3;
  }

  private async fetchWithRetry(
    url: string,
    options: RequestInit,
    retriesLeft: number = this.retries
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok && retriesLeft > 0 && response.status >= 500) {
        await new Promise((r) => setTimeout(r, 1000 * (this.retries - retriesLeft + 1)));
        return this.fetchWithRetry(url, options, retriesLeft - 1);
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);

      if (retriesLeft > 0 && error instanceof Error && error.name !== 'AbortError') {
        await new Promise((r) => setTimeout(r, 1000 * (this.retries - retriesLeft + 1)));
        return this.fetchWithRetry(url, options, retriesLeft - 1);
      }

      throw error;
    }
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    return headers;
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, value);
        }
      });
    }

    const response = await this.fetchWithRetry(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<T>(response);
  }

  async post<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
    const response = await this.fetchWithRetry(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async put<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
    const response = await this.fetchWithRetry(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async delete<T>(path: string): Promise<ApiResponse<T>> {
    const response = await this.fetchWithRetry(`${this.baseUrl}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    return this.handleResponse<T>(response);
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const data = (await response.json()) as Record<string, unknown>;

    if (!response.ok) {
      throw new XcapitSDKError({
        code: (data.code as string) || `HTTP_${response.status}`,
        message: (data.message as string) || response.statusText,
        details: data.details as Record<string, unknown> | undefined,
      });
    }

    return {
      success: true,
      data: (data.data ?? data) as T,
      meta: data.meta as ResponseMeta | undefined,
    };
  }
}

/**
 * Main SDK Client for Xcapit FHE-ML Platform
 *
 * @example
 * ```typescript
 * import { XcapitClient } from '@xcapit/fhe-ml-sdk';
 *
 * const client = new XcapitClient({
 *   apiUrl: 'https://api.xcapit.io',
 *   apiKey: 'your-api-key',
 * });
 *
 * // Create and train a model
 * const model = await client.models.create({
 *   name: 'My Model',
 *   type: ModelType.LinearRegression,
 * });
 *
 * // Make predictions
 * const prediction = await client.predictions.predict({
 *   modelId: model.id,
 *   encryptedInput: encryptedData,
 * });
 * ```
 */
export class XcapitClient {
  private http: HttpClient;

  public readonly models: ModelsAPI;
  public readonly predictions: PredictionsAPI;
  public readonly encryption: EncryptionAPI;
  public readonly consortiums: ConsortiumsAPI;
  public readonly governance: GovernanceAPI;
  public readonly compliance: ComplianceAPI;
  public readonly dataQuality: DataQualityAPI;
  public readonly explainability: ExplainabilityAPI;

  constructor(config: SDKConfig) {
    this.http = new HttpClient(config);

    this.models = new ModelsAPI(this.http);
    this.predictions = new PredictionsAPI(this.http);
    this.encryption = new EncryptionAPI(this.http);
    this.consortiums = new ConsortiumsAPI(this.http);
    this.governance = new GovernanceAPI(this.http);
    this.compliance = new ComplianceAPI(this.http);
    this.dataQuality = new DataQualityAPI(this.http);
    this.explainability = new ExplainabilityAPI(this.http);
  }

  /**
   * Health check for the API
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await this.http.get<{ status: string; version: string }>('/health');
    return response.data!;
  }
}

/**
 * Models API
 */
class ModelsAPI {
  constructor(private http: HttpClient) {}

  async list(params?: PaginationParams): Promise<ApiResponse<Model[]>> {
    return this.http.get('/models', params as Record<string, string>);
  }

  async get(modelId: string): Promise<Model> {
    const response = await this.http.get<Model>(`/models/${modelId}`);
    return response.data!;
  }

  async create(request: CreateModelRequest): Promise<Model> {
    const response = await this.http.post<Model>('/models', request);
    return response.data!;
  }

  async train(request: TrainModelRequest): Promise<TrainingResult> {
    const response = await this.http.post<TrainingResult>(
      `/models/${request.modelId}/train`,
      request
    );
    return response.data!;
  }

  async delete(modelId: string): Promise<void> {
    await this.http.delete(`/models/${modelId}`);
  }

  async getTrainingStatus(modelId: string): Promise<{
    status: string;
    progress: number;
    currentEpoch?: number;
    totalEpochs?: number;
  }> {
    const response = await this.http.get<{
      status: string;
      progress: number;
      currentEpoch?: number;
      totalEpochs?: number;
    }>(`/models/${modelId}/training-status`);
    return response.data!;
  }
}

/**
 * Predictions API
 */
class PredictionsAPI {
  constructor(private http: HttpClient) {}

  async predict(request: PredictionRequest): Promise<PredictionResponse> {
    const response = await this.http.post<PredictionResponse>('/predict', request);
    return response.data!;
  }

  async predictBatch(request: BatchPredictionRequest): Promise<BatchPredictionResponse> {
    const response = await this.http.post<BatchPredictionResponse>('/predict/batch', request);
    return response.data!;
  }

  async get(predictionId: string): Promise<PredictionResponse> {
    const response = await this.http.get<PredictionResponse>(`/predictions/${predictionId}`);
    return response.data!;
  }

  async list(
    modelId?: string,
    params?: PaginationParams
  ): Promise<ApiResponse<PredictionResponse[]>> {
    const queryParams: Record<string, string> = {
      ...(params as Record<string, string>),
    };
    if (modelId) {
      queryParams.modelId = modelId;
    }
    return this.http.get('/predictions', queryParams);
  }
}

/**
 * Encryption API
 */
class EncryptionAPI {
  constructor(private http: HttpClient) {}

  async createContext(): Promise<EncryptionContext> {
    const response = await this.http.post<EncryptionContext>('/encryption/context');
    return response.data!;
  }

  async getContext(contextId: string): Promise<EncryptionContext> {
    const response = await this.http.get<EncryptionContext>(`/encryption/context/${contextId}`);
    return response.data!;
  }

  async encrypt(request: EncryptRequest): Promise<EncryptedData> {
    const response = await this.http.post<EncryptedData>('/encryption/encrypt', request);
    return response.data!;
  }

  async getPublicKey(contextId: string): Promise<string> {
    const response = await this.http.get<{ publicKey: string }>(
      `/encryption/context/${contextId}/public-key`
    );
    return response.data!.publicKey;
  }
}

/**
 * Consortiums API
 */
class ConsortiumsAPI {
  constructor(private http: HttpClient) {}

  async list(params?: PaginationParams): Promise<ApiResponse<Consortium[]>> {
    return this.http.get('/consortiums', params as Record<string, string>);
  }

  async get(consortiumId: string): Promise<Consortium> {
    const response = await this.http.get<Consortium>(`/consortiums/${consortiumId}`);
    return response.data!;
  }

  async create(request: CreateConsortiumRequest): Promise<Consortium> {
    const response = await this.http.post<Consortium>('/consortiums', request);
    return response.data!;
  }

  async getMembers(consortiumId: string): Promise<ConsortiumMember[]> {
    const response = await this.http.get<ConsortiumMember[]>(
      `/consortiums/${consortiumId}/members`
    );
    return response.data!;
  }

  async addMember(consortiumId: string, memberAddress: string): Promise<void> {
    await this.http.post(`/consortiums/${consortiumId}/members`, { address: memberAddress });
  }

  async recordContribution(request: RecordContributionRequest): Promise<Contribution> {
    const response = await this.http.post<Contribution>(
      `/consortiums/${request.consortiumId}/contributions`,
      request
    );
    return response.data!;
  }

  async getContributions(consortiumId: string): Promise<Contribution[]> {
    const response = await this.http.get<Contribution[]>(
      `/consortiums/${consortiumId}/contributions`
    );
    return response.data!;
  }

  async startTraining(consortiumId: string): Promise<{ trainingId: string }> {
    const response = await this.http.post<{ trainingId: string }>(
      `/consortiums/${consortiumId}/train`
    );
    return response.data!;
  }
}

/**
 * Governance API
 */
class GovernanceAPI {
  constructor(private http: HttpClient) {}

  async createProposal(request: CreateProposalRequest): Promise<Proposal> {
    const response = await this.http.post<Proposal>('/governance/proposals', request);
    return response.data!;
  }

  async getProposal(proposalId: string): Promise<Proposal> {
    const response = await this.http.get<Proposal>(`/governance/proposals/${proposalId}`);
    return response.data!;
  }

  async listProposals(consortiumId: string): Promise<Proposal[]> {
    const response = await this.http.get<Proposal[]>(
      `/governance/proposals?consortiumId=${consortiumId}`
    );
    return response.data!;
  }

  async vote(request: VoteRequest): Promise<void> {
    await this.http.post(`/governance/proposals/${request.proposalId}/vote`, {
      support: request.support,
    });
  }

  async executeProposal(proposalId: string): Promise<void> {
    await this.http.post(`/governance/proposals/${proposalId}/execute`);
  }

  async getAuditTrail(consortiumId: string): Promise<AuditEvent[]> {
    const response = await this.http.get<AuditEvent[]>(
      `/governance/audit-trail?consortiumId=${consortiumId}`
    );
    return response.data!;
  }

  async verifyAuditTrail(consortiumId: string): Promise<{ valid: boolean; hash: string }> {
    const response = await this.http.get<{ valid: boolean; hash: string }>(
      `/governance/audit-trail/${consortiumId}/verify`
    );
    return response.data!;
  }
}

/**
 * Compliance API
 */
class ComplianceAPI {
  constructor(private http: HttpClient) {}

  async generateReport(request: GenerateReportRequest): Promise<ComplianceReport> {
    const response = await this.http.post<ComplianceReport>('/compliance/reports', request);
    return response.data!;
  }

  async getReport(reportId: string): Promise<ComplianceReport> {
    const response = await this.http.get<ComplianceReport>(`/compliance/reports/${reportId}`);
    return response.data!;
  }

  async listReports(params?: PaginationParams): Promise<ApiResponse<ComplianceReport[]>> {
    return this.http.get('/compliance/reports', params as Record<string, string>);
  }

  async checkCompliance(
    framework: string,
    modelId?: string
  ): Promise<{ compliant: boolean; issues: string[] }> {
    const response = await this.http.get<{ compliant: boolean; issues: string[] }>(
      `/compliance/check?framework=${framework}${modelId ? `&modelId=${modelId}` : ''}`
    );
    return response.data!;
  }
}

/**
 * Data Quality API
 */
class DataQualityAPI {
  constructor(private http: HttpClient) {}

  async analyzeDataset(
    datasetId: string,
    encryptedSample?: string
  ): Promise<DataQualityReport> {
    const response = await this.http.post<DataQualityReport>('/data-quality/analyze', {
      datasetId,
      encryptedSample,
    });
    return response.data!;
  }

  async getReport(reportId: string): Promise<DataQualityReport> {
    const response = await this.http.get<DataQualityReport>(`/data-quality/reports/${reportId}`);
    return response.data!;
  }

  async validateSchema(
    schema: Record<string, string>,
    sampleData: unknown[]
  ): Promise<{ valid: boolean; errors: string[] }> {
    const response = await this.http.post<{ valid: boolean; errors: string[] }>(
      '/data-quality/validate-schema',
      { schema, sampleData }
    );
    return response.data!;
  }
}

/**
 * Explainability API
 */
class ExplainabilityAPI {
  constructor(private http: HttpClient) {}

  async explain(request: ExplanationRequest): Promise<Explanation> {
    const response = await this.http.post<Explanation>('/explainability/explain', request);
    return response.data!;
  }

  async getExplanation(explanationId: string): Promise<Explanation> {
    const response = await this.http.get<Explanation>(`/explainability/${explanationId}`);
    return response.data!;
  }

  async getFeatureImportance(modelId: string): Promise<{ features: string[]; importances: number[] }> {
    const response = await this.http.get<{ features: string[]; importances: number[] }>(
      `/explainability/feature-importance/${modelId}`
    );
    return response.data!;
  }
}

export default XcapitClient;
