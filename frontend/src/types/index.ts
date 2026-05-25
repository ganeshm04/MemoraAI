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

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  tokens_used?: number;
  chunks?: RetrievedChunk[];
}

export interface MemoryEntry {
  id: number;
  role?: string;
  content: string;
  token_count?: number;
  created_at?: string;
}

export interface UserFact {
  id: number;
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
  session_id: string;
  summary: string;
  key_topics: string[];
  important_facts: string[];
  sentiment: string;
  duration_minutes: number;
  message_count: number;
  created_at?: string;
}

export interface SearchResult {
  id: number;
  content: string;
  source: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface IngestionResult {
  success: boolean;
  source: string;
  source_type: string;
  chunks_created: number;
  text_length: number;
  errors: string[];
}

export interface MemoryStats {
  episodic: {
    total_episodes: number;
    total_messages: number;
    total_duration_minutes: number;
    avg_messages_per_session: number;
    unique_sessions: number;
  };
  long_term_facts_count: number;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sessionId: string;
  error: string | null;
}

export interface RetrievalState {
  chunks: RetrievedChunk[];
  isLoading: boolean;
}

export interface MemoryState {
  shortTerm: MemoryEntry[];
  longTerm: UserFact[];
  episodic: Episode[];
  stats: MemoryStats | null;
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