// API Types matching backend schemas

export interface DocumentMetadata {
  file_name: string;
  page?: number;
  source?: string;
}

export interface SourceDocument {
  content: string;
  score: number;
  metadata: DocumentMetadata;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
}

export interface QueryResponse {
  chat_response: string;
  source_documents: SourceDocument[];
}

export interface QueryHistoryResponse {
  id: string;
  query: string;
  chat_response: string;
  top_k: number;
  response_time_ms: number | null;
  source_document_count: number;
  created_at: string;
  success: boolean;
  error_message: string | null;
}

export interface SourceDocumentHistoryResponse {
  id: string;
  content_preview: string;
  similarity_score: number;
  document_metadata: DocumentMetadata | null;
  created_at: string;
}

export interface QueryHistoryListResponse {
  items: QueryHistoryResponse[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface QueryDetailResponse {
  query_history: QueryHistoryResponse;
  source_documents: SourceDocumentHistoryResponse[];
}

export interface QueryStatisticsResponse {
  total_queries: number;
  successful_queries: number;
  success_rate_percent: number;
  average_response_time_ms: number | null;
}

export interface HealthStatusResponse {
  vector_store: boolean;
  embedding_model: boolean;
  chat_model: boolean;
  index_status?: boolean;
}

export interface DocumentCountResponse {
  document_count: number;
  message: string;
}

// Frontend-specific types
export interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: string;
  source_documents?: SourceDocument[];
}

export interface ChatSession {
  id: string;
  name: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}