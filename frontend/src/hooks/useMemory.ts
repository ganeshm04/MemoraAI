import { create } from 'zustand';
import type { MemoryEntry, UserFact, Episode, MemoryStats } from '@/types';

interface MemoryStore {
  shortTerm: MemoryEntry[];
  longTerm: UserFact[];
  episodic: Episode[];
  stats: MemoryStats | null;
  isLoading: boolean;
  error: string | null;
  
  setShortTerm: (entries: MemoryEntry[]) => void;
  addShortTerm: (entry: MemoryEntry) => void;
  setLongTerm: (facts: UserFact[]) => void;
  addLongTerm: (fact: UserFact) => void;
  removeLongTerm: (id: number) => void;
  setEpisodic: (episodes: Episode[]) => void;
  addEpisodic: (episode: Episode) => void;
  setStats: (stats: MemoryStats) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMemory: () => void;
}

export const useMemoryStore = create<MemoryStore>((set) => ({
  shortTerm: [],
  longTerm: [],
  episodic: [],
  stats: null,
  isLoading: false,
  error: null,

  setShortTerm: (entries) => set({ shortTerm: entries }),

  addShortTerm: (entry) =>
    set((state) => ({
      shortTerm: [...state.shortTerm, entry],
    })),

  setLongTerm: (facts) => set({ longTerm: facts }),

  addLongTerm: (fact) =>
    set((state) => ({
      longTerm: [...state.longTerm, fact],
    })),

  removeLongTerm: (id) =>
    set((state) => ({
      longTerm: state.longTerm.filter((f) => f.id !== id),
    })),

  setEpisodic: (episodes) => set({ episodic: episodes }),

  addEpisodic: (episode) =>
    set((state) => ({
      episodic: [episode, ...state.episodic],
    })),

  setStats: (stats) => set({ stats }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearMemory: () =>
    set({
      shortTerm: [],
      longTerm: [],
      episodic: [],
      stats: null,
      isLoading: false,
      error: null,
    }),
}));