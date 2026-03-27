import { create } from 'zustand';
import * as api from '../api/client';
import type { LibraryModel } from '../types';

interface LibraryStore {
  models: LibraryModel[];
  allTags: string[];
  activeTag: string | null;
  groupByTag: boolean;
  loading: boolean;
  error: string | null;
  fetchModels: (params?: { search?: string; tag?: string }) => Promise<void>;
  fetchTags: () => Promise<void>;
  addModel: (data: Partial<LibraryModel>) => Promise<LibraryModel>;
  importFromURL: (url: string) => Promise<LibraryModel>;
  updateTags: (id: number, tags: string[]) => Promise<void>;
  deleteModel: (id: number) => Promise<void>;
  setActiveTag: (tag: string | null) => void;
  setGroupByTag: (v: boolean) => void;
}

export const useLibraryStore = create<LibraryStore>((set, get) => ({
  models: [],
  allTags: [],
  activeTag: null,
  groupByTag: false,
  loading: false,
  error: null,

  fetchModels: async (params) => {
    set({ loading: true, error: null });
    try {
      const models = await api.getLibrary(params);
      set({ models, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  fetchTags: async () => {
    try {
      const allTags = await api.getAllTags();
      set({ allTags });
    } catch {
      // non-critical
    }
  },

  addModel: async (data) => {
    const model = await api.addToLibrary(data);
    set((state) => ({ models: [model, ...state.models] }));
    return model;
  },

  importFromURL: async (url) => {
    const model = await api.importFromURL(url);
    set((state) => ({ models: [model, ...state.models] }));
    return model;
  },

  updateTags: async (id, tags) => {
    const model = await api.updateLibraryTags(id, tags);
    set((state) => ({
      models: state.models.map((m) => (m.id === id ? model : m)),
    }));
    // Refresh global tag list
    get().fetchTags();
  },

  deleteModel: async (id) => {
    await api.deleteLibraryModel(id);
    set((state) => ({ models: state.models.filter((m) => m.id !== id) }));
  },

  setActiveTag: (tag) => set({ activeTag: tag }),
  setGroupByTag: (v) => set({ groupByTag: v }),
}));
