import useSWR from "swr";
import { useState } from "react";
import { apiClient, fetcher } from "@/lib/api-client";
import type {
  QueryHistoryListResponse,
  QueryDetailResponse,
  QueryStatisticsResponse,
  HealthStatusResponse,
  DocumentCountResponse,
  QueryRequest,
  QueryResponse,
  Message,
} from "@/types/api";

// Hook for fetching query history
export const useQueryHistory = (limit = 10, offset = 0) => {
  const { data, error, isLoading, mutate } = useSWR<QueryHistoryListResponse>(
    `/history/queries?limit=${limit}&offset=${offset}`,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
    }
  );

  return {
    queryHistory: data,
    isLoading,
    isError: error,
    mutate,
  };
};

// Hook for fetching a specific query
export const useQuery = (queryId: string | null) => {
  const { data, error, isLoading } = useSWR<QueryDetailResponse>(
    queryId ? `/history/queries/${queryId}` : null,
    fetcher
  );

  return {
    query: data,
    isLoading,
    isError: error,
  };
};

// Hook for fetching query statistics
export const useQueryStatistics = () => {
  const { data, error, isLoading } = useSWR<QueryStatisticsResponse>(
    "/history/statistics",
    fetcher
  );

  return {
    statistics: data,
    isLoading,
    isError: error,
  };
};

// Hook for fetching RAG health status
export const useRAGHealth = (includeIndex = false) => {
  const { data, error, isLoading } = useSWR<HealthStatusResponse>(
    `/rag/health?include_index=${includeIndex}`,
    fetcher
  );

  return {
    health: data,
    isLoading,
    isError: error,
  };
};

// Hook for fetching document count
export const useDocumentCount = () => {
  const { data, error, isLoading } = useSWR<DocumentCountResponse>(
    "/rag/documents/count",
    fetcher
  );

  return {
    documentCount: data,
    isLoading,
    isError: error,
  };
};

// Hook for sending messages (mutation)
export const useQueryRAG = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendQuery = async (
    queryRequest: QueryRequest
  ): Promise<QueryResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.queryRAG(queryRequest);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    sendQuery,
    isLoading,
    error,
  };
};

// Utility function to convert QueryResponse to Message
export const convertQueryResponseToMessages = (
  userQuery: string,
  response: QueryResponse,
  baseMessageId: string
): Message[] => {
  const timestamp = new Date().toISOString();
  
  return [
    {
      id: `${baseMessageId}-user`,
      type: "user" as const,
      content: userQuery,
      timestamp,
    },
    {
      id: `${baseMessageId}-assistant`,
      type: "assistant" as const,
      content: response.chat_response,
      timestamp,
      source_documents: response.source_documents,
    },
  ];
};

// Utility function to convert QueryHistoryResponse to simplified chat list
export const convertQueryHistoryToChats = (
  queryHistory: QueryHistoryListResponse
) => {
  return queryHistory.items.map((item) => ({
    id: item.id,
    name: item.query.length > 30 ? `${item.query.substring(0, 30)}...` : item.query,
    created_at: item.created_at,
    success: item.success,
  }));
};