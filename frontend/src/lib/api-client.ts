import type {
  QueryRequest,
  QueryResponse,
  QueryHistoryListResponse,
  QueryDetailResponse,
  QueryStatisticsResponse,
  HealthStatusResponse,
  DocumentCountResponse,
} from "@/types/api";

// API Configuration
// In production (when served by FastAPI), use relative URLs
// In development, use environment variable or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// API Client with error handling
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || 
          errorData.detail || 
          `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("An unexpected error occurred");
    }
  }

  // RAG endpoints
  async queryRAG(queryRequest: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>("/rag/query", {
      method: "POST",
      body: JSON.stringify(queryRequest),
    });
  }

  async getRAGHealth(includeIndex = false): Promise<HealthStatusResponse> {
    const params = includeIndex ? "?include_index=true" : "";
    return this.request<HealthStatusResponse>(`/rag/health${params}`);
  }

  async getDocumentCount(): Promise<DocumentCountResponse> {
    return this.request<DocumentCountResponse>("/rag/documents/count");
  }

  // History endpoints
  async getQueryHistory(
    limit = 10,
    offset = 0
  ): Promise<QueryHistoryListResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    return this.request<QueryHistoryListResponse>(
      `/history/queries?${params}`
    );
  }

  async getQueryById(queryId: string): Promise<QueryDetailResponse> {
    return this.request<QueryDetailResponse>(`/history/queries/${queryId}`);
  }

  async getQueryStatistics(): Promise<QueryStatisticsResponse> {
    return this.request<QueryStatisticsResponse>("/history/statistics");
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.request("/health");
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// SWR fetcher function
export const fetcher = async (url: string) => {
  const response = await fetch(`${API_BASE_URL}${url}`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.message || 
      errorData.detail || 
      `HTTP ${response.status}: ${response.statusText}`
    );
  }
  
  return response.json();
};

export default apiClient;