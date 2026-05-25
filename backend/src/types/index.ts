export interface SearchResult {
  id: number;
  content: string;
  source: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface RetrievedChunk {
  id: number;
  content: string;
  source: string;
  fused_score: number;
  vector_score?: number;
  bm25_score?: number;
  rerank_score?: number;
}

export interface QueryResponse {
  response: string;
  session_id: string;
  query_type: string;
  chunks: RetrievedChunk[];
  tokens_used: number;
  sources: string[];
}

export interface IngestionResult {
  success: boolean;
  source: string;
  source_type: string;
  chunks_created: number;
  text_length: number;
  errors: string[];
}

export interface MemoryEntry {
  id: number;
  session_id?: string;
  user_id?: string;
  role?: string;
  content: string;
  token_count?: number;
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface UserFact {
  id: number;
  user_id: string;
  key: string;
  value: string;
  category: string;
  confidence: number;
  source: string;
  created_at?: string;
  updated_at?: string;
}

export interface Episode {
  id: number;
  user_id: string;
  session_id: string;
  summary: string;
  key_topics: string[];
  important_facts: string[];
  sentiment: string;
  duration_minutes: number;
  message_count: number;
  created_at?: string;
}

export type QueryType = 'conversational' | 'factual' | 'analytical' | 'memory_related';

export interface ErrorResponse {
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;
  path: string;
  requestId: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface SortParams {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}