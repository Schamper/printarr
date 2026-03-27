import { create } from 'zustand';
import * as api from '../api/client';
import type { QueueItem } from '../types';

interface QueueStore {
  items: QueueItem[];
  loading: boolean;
  error: string | null;
  fetchItems: () => Promise<void>;
  addItem: (data: {
    file_id: number;
    notes?: string;
    filament_type?: string;
    filament_color?: string;
    copies?: number;
  }) => Promise<QueueItem>;
  updateItem: (id: number, data: Partial<QueueItem>) => Promise<void>;
  removeItem: (id: number) => Promise<void>;
  reorderItems: (orderedIds: number[]) => Promise<void>;
}

export const useQueueStore = create<QueueStore>((set) => ({
  items: [],
  loading: false,
  error: null,

  fetchItems: async () => {
    set({ loading: true, error: null });
    try {
      const items = await api.getQueue();
      set({ items, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  addItem: async (data) => {
    const item = await api.addToQueue(data);
    set((state) => ({ items: [...state.items, item] }));
    return item;
  },

  updateItem: async (id, data) => {
    const updated = await api.updateQueueItem(id, data);
    set((state) => ({
      items: state.items.map((i) => (i.id === id ? updated : i)),
    }));
  },

  removeItem: async (id) => {
    await api.removeFromQueue(id);
    set((state) => ({ items: state.items.filter((i) => i.id !== id) }));
  },

  reorderItems: async (orderedIds) => {
    const reorderData = orderedIds.map((id, i) => ({ id, sort_order: i }));
    // Optimistic reorder
    set((state) => {
      const byId = new Map(state.items.map((i) => [i.id, i]));
      const reordered = orderedIds
        .map((id, i) => {
          const item = byId.get(id);
          return item ? { ...item, sort_order: i } : null;
        })
        .filter(Boolean) as QueueItem[];
      return { items: reordered };
    });
    await api.reorderQueue(reorderData);
  },
}));
