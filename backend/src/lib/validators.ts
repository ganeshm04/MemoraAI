import { z } from 'zod';

export const ingestPDFSchema = z.object({
  file_path: z.string().min(1),
  metadata: z.record(z.any()).optional(),
  chunk_size: z.number().min(100).max(2000).default(700),
  chunk_overlap: z.number().min(0).max(500).default(100),
});

export const ingestURLSchema = z.object({
  url: z.string().url(),
  metadata: z.record(z.any()).optional(),
  chunk_size: z.number().min(100).max(2000).default(700),
  chunk_overlap: z.number().min(0).max(500).default(100),
});

export const ingestTextSchema = z.object({
  text: z.string().min(1).max(1_000_000),
  source: z.string().min(1),
  metadata: z.record(z.any()).optional(),
  chunk_size: z.number().min(100).max(2000).default(700),
  chunk_overlap: z.number().min(0).max(500).default(100),
});

export const querySchema = z.object({
  query: z.string().min(1).max(1000),
  session_id: z.string().min(1),
  user_id: z.string().optional(),
  use_memory: z.boolean().default(true),
  use_reranking: z.boolean().default(true),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().min(1).max(8192).default(2048),
});

export const conversationalQuerySchema = z.object({
  query: z.string().min(1).max(1000),
  session_id: z.string().min(1),
  user_id: z.string().optional(),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().min(1).max(8192).default(2048),
});

export const vectorSearchSchema = z.object({
  query: z.string().min(1),
  top_k: z.number().min(1).max(100).default(10),
  threshold: z.number().min(0).max(1).default(0.7),
  table: z.string().default('chunks'),
});

export const bm25SearchSchema = z.object({
  query: z.string().min(1),
  top_k: z.number().min(1).max(100).default(10),
  table: z.string().default('chunks'),
});

export const hybridSearchSchema = z.object({
  query: z.string().min(1),
  top_k: z.number().min(1).max(50).default(10),
  use_reranking: z.boolean().default(true),
  weights: z.object({
    vector: z.number().optional(),
    bm25: z.number().optional(),
  }).optional(),
});

export const rerankSchema = z.object({
  query: z.string().min(1),
  documents: z.array(
    z.object({
      content: z.string(),
      metadata: z.record(z.any()).optional(),
    }),
  ).min(1),
  top_k: z.number().min(1).max(50).default(5),
});

export const addMemorySchema = z.object({
  session_id: z.string().min(1),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string().min(1),
  metadata: z.record(z.any()).optional(),
});

export const storeFactSchema = z.object({
  user_id: z.string().min(1),
  key: z.string().min(1),
  value: z.string().min(1),
  category: z.string().default('general'),
  confidence: z.number().min(0).max(1).default(1.0),
  source: z.string().default('conversation'),
});

export const createEpisodeSchema = z.object({
  user_id: z.string().min(1),
  session_id: z.string().min(1),
  summary: z.string().min(1),
  key_topics: z.array(z.string()).default([]),
  important_facts: z.array(z.string()).default([]),
  sentiment: z.string().default('neutral'),
  duration_minutes: z.number().default(0),
  message_count: z.number().default(0),
});

export type IngestPDFInput = z.infer<typeof ingestPDFSchema>;
export type IngestURLInput = z.infer<typeof ingestURLSchema>;
export type IngestTextInput = z.infer<typeof ingestTextSchema>;
export type QueryInput = z.infer<typeof querySchema>;
export type ConversationalQueryInput = z.infer<typeof conversationalQuerySchema>;
export type VectorSearchInput = z.infer<typeof vectorSearchSchema>;
export type BM25SearchInput = z.infer<typeof bm25SearchSchema>;
export type HybridSearchInput = z.infer<typeof hybridSearchSchema>;
export type RerankInput = z.infer<typeof rerankSchema>;
export type AddMemoryInput = z.infer<typeof addMemorySchema>;
export type StoreFactInput = z.infer<typeof storeFactSchema>;
export type CreateEpisodeInput = z.infer<typeof createEpisodeSchema>;