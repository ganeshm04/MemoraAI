import { create } from 'zustand';
import type { RetrievedChunk, SearchResult } from '@/types';

interface RetrievalStore {
  chunks: RetrievedChunk[];
  searchResults: SearchResult[];
  isLoading: boolean;
  lastQuery: string;
  
  setChunks: (chunks: RetrievedChunk[]) => void;
  setSearchResults: (results: SearchResult[]) => void;
  setLoading: (loading: boolean) => void;
  setLastQuery: (query: string) => void;
  clearRetrieval: () => void;
}

export const useRetrievalStore = create<RetrievalStore>((set) => ({
  chunks: [],
  searchResults: [],
  isLoading: false,
  lastQuery: '',

  setChunks: (chunks) => set({ chunks }),

  setSearchResults: (results) => set({ searchResults: results }),

  setLoading: (loading) => set({ isLoading: loading }),

  setLastQuery: (query) => set({ lastQuery: query }),

  clearRetrieval: () =>
    set({
      chunks: [],
      searchResults: [],
      isLoading: false,
      lastQuery: '',
    }),
}));