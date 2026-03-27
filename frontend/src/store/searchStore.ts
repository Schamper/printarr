import { create } from 'zustand';
import type { SearchResult, SourceState } from '../types';

export type SortOption = 'relevance' | 'downloads' | 'likes' | 'newest';

interface SearchStore {
  query: string;
  page: number;
  sort: SortOption;
  results: SearchResult[];
  sourceStates: Record<string, SourceState>;
  isSearching: boolean;
  hasMore: boolean;
  setQuery: (q: string) => void;
  setSort: (s: SortOption) => void;
  startSearch: (query: string, sources?: string[]) => void;
  loadMore: () => void;
  clearResults: () => void;
}

let activeEventSource: EventSource | null = null;

function closeActive() {
  if (activeEventSource) {
    activeEventSource.close();
    activeEventSource = null;
  }
}

function connectSSE(
  params: URLSearchParams,
  set: (fn: (state: SearchStore) => Partial<SearchStore>) => void,
  append: boolean,
) {
  closeActive();

  const eventSource = new EventSource(`/api/search?${params}`);
  activeEventSource = eventSource;

  // Track how many results arrived in this page to determine hasMore
  let pageResultCount = 0;

  eventSource.addEventListener('source_start', (e) => {
    const { source, display_name, configured = true } = JSON.parse(e.data);
    set((state) => ({
      sourceStates: {
        ...state.sourceStates,
        [source]: {
          name: display_name,
          status: configured ? 'searching' : 'idle',
          resultCount: append ? (state.sourceStates[source]?.resultCount || 0) : 0,
          configured,
        },
      },
    }));
  });

  eventSource.addEventListener('result', (e) => {
    const result: SearchResult = JSON.parse(e.data);
    pageResultCount++;
    set((state) => {
      const ss = state.sourceStates[result.source];
      return {
        results: [...state.results, result],
        sourceStates: {
          ...state.sourceStates,
          [result.source]: ss
            ? { ...ss, resultCount: ss.resultCount + 1 }
            : { name: result.source, status: 'searching', resultCount: 1, configured: true },
        },
      };
    });
  });

  eventSource.addEventListener('source_done', (e) => {
    const { source } = JSON.parse(e.data);
    set((state) => {
      const updated = { ...state.sourceStates };
      if (updated[source]) {
        updated[source] = { ...updated[source], status: 'done' };
      }
      return { sourceStates: updated };
    });
  });

  eventSource.addEventListener('source_error', (e) => {
    const { source, display_name } = JSON.parse(e.data);
    set((state) => ({
      sourceStates: {
        ...state.sourceStates,
        [source]: {
          name: display_name,
          status: 'error',
          resultCount: state.sourceStates[source]?.resultCount || 0,
          configured: state.sourceStates[source]?.configured ?? true,
        },
      },
    }));
  });

  eventSource.addEventListener('done', () => {
    eventSource.close();
    if (activeEventSource === eventSource) activeEventSource = null;
    set((state) => {
      const updated = { ...state.sourceStates };
      for (const key of Object.keys(updated)) {
        if (updated[key].status === 'searching') {
          updated[key] = { ...updated[key], status: 'done' };
        }
      }
      return { isSearching: false, sourceStates: updated, hasMore: pageResultCount > 0 };
    });
  });

  eventSource.onerror = () => {
    eventSource.close();
    if (activeEventSource === eventSource) activeEventSource = null;
    set(() => ({ isSearching: false, hasMore: false }));
  };
}

export const useSearchStore = create<SearchStore>((set, get) => ({
  query: '',
  page: 1,
  sort: 'relevance' as SortOption,
  results: [],
  sourceStates: {},
  isSearching: false,
  hasMore: true,

  setQuery: (q) => set({ query: q }),

  setSort: (s) => {
    const { query, sort } = get();
    if (s === sort) return;
    set({ sort: s });
    // Re-search if we already have a query
    if (query) get().startSearch(query);
  },

  clearResults: () => {
    closeActive();
    set({ results: [], sourceStates: {}, isSearching: false, page: 1, hasMore: true });
  },

  startSearch: (query, sources) => {
    closeActive();
    const { sort } = get();
    set({ results: [], sourceStates: {}, isSearching: true, query, page: 1, hasMore: true });

    const params = new URLSearchParams({ q: query, page: '1', sort });
    if (sources?.length) params.set('sources', sources.join(','));

    connectSSE(params, set, false);
  },

  loadMore: () => {
    const { query, page, sort, isSearching, hasMore } = get();
    if (isSearching || !hasMore || !query) return;

    const nextPage = page + 1;
    set({ isSearching: true, page: nextPage });

    const params = new URLSearchParams({ q: query, page: String(nextPage), sort });
    connectSSE(params, set, true);
  },
}));
