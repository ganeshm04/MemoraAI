import { create } from 'zustand';
import type { Message, RetrievedChunk } from '@/types';
import { generateId } from '@/lib/utils';

interface ChatStore {
  messages: Message[];
  isLoading: boolean;
  sessionId: string;
  error: string | null;
  selectedChunks: RetrievedChunk[];
  sources: string[];
  
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setChunks: (chunks: RetrievedChunk[]) => void;
  setSources: (sources: string[]) => void;
  clearChat: () => void;
  resetSession: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  sessionId: generateId(),
  error: null,
  selectedChunks: [],
  sources: [],

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: generateId(),
          timestamp: new Date(),
        },
      ],
    })),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  setChunks: (chunks) => set({ selectedChunks: chunks }),

  setSources: (sources) => set({ sources }),

  clearChat: () =>
    set((state) => ({
      messages: [],
      error: null,
      selectedChunks: [],
      sources: [],
    })),

  resetSession: () =>
    set({
      messages: [],
      isLoading: false,
      error: null,
      selectedChunks: [],
      sources: [],
      sessionId: generateId(),
    }),
}));