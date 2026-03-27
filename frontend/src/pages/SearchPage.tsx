import { ArrowDownWideNarrow, Loader2, Search as SearchIcon } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ModelCard from '../components/ModelCard';
import SearchBar from '../components/SearchBar';
import SourceProgress from '../components/SourceProgress';
import { type SortOption, useSearchStore } from '../store/searchStore';
import type { SearchResult } from '../types';

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'downloads', label: 'Downloads' },
  { value: 'likes', label: 'Likes' },
  { value: 'newest', label: 'Newest' },
];

function sortResults(results: SearchResult[], sort: SortOption): SearchResult[] {
  if (sort === 'relevance') return results;
  return [...results].sort((a, b) => {
    switch (sort) {
      case 'downloads': return b.download_count - a.download_count;
      case 'likes': return b.like_count - a.like_count;
      case 'newest': return (b.published_at || '').localeCompare(a.published_at || '');
      default: return 0;
    }
  });
}

export default function SearchPage() {
  const { results, sourceStates, isSearching, hasMore, sort, startSearch, loadMore, setSort } = useSearchStore();
  const [sourceFilter, setSourceFilter] = useState<Set<string>>(new Set());
  const sortedResults = useMemo(() => sortResults(results, sort), [results, sort]);
  const filteredResults = useMemo(
    () => (sourceFilter.size > 0 ? sortedResults.filter((r) => sourceFilter.has(r.source)) : sortedResults),
    [sortedResults, sourceFilter],
  );
  const sentinelRef = useRef<HTMLDivElement>(null);
  const isIntersectingRef = useRef(false);

  const handleSourceClick = (sourceName: string) => {
    setSourceFilter((prev) => {
      const next = new Set(prev);
      if (next.has(sourceName)) next.delete(sourceName);
      else next.add(sourceName);
      return next;
    });
  };

  const handleIntersect = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      isIntersectingRef.current = entries[0].isIntersecting;
      if (entries[0].isIntersecting) {
        loadMore();
      }
    },
    [loadMore],
  );

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(handleIntersect, {
      rootMargin: '400px',
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [handleIntersect]);

  // Re-trigger load when a page finishes but sentinel is still in view
  useEffect(() => {
    if (!isSearching && hasMore && isIntersectingRef.current) {
      loadMore();
    }
  }, [isSearching, hasMore, loadMore]);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Search</h1>
      </div>

      <div className="search-controls">
        <SearchBar onSearch={(q) => startSearch(q)} isSearching={isSearching} />
        <div className="sort-control">
          <ArrowDownWideNarrow size={16} />
          <select
            className="select"
            value={sort}
            onChange={(e) => setSort(e.target.value as SortOption)}
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ marginTop: 20 }}>
        <SourceProgress
          sources={sourceStates}
          isSearching={isSearching}
          activeFilter={sourceFilter}
          onSourceClick={handleSourceClick}
        />
      </div>

      {filteredResults.length > 0 ? (
        <>
          <div className="card-grid" style={{ marginTop: 8 }}>
            {filteredResults.map((r, i) => (
              <ModelCard key={`${r.source}-${r.source_id}-${i}`} result={r} />
            ))}
          </div>

          {/* Infinite-scroll sentinel */}
          <div ref={sentinelRef} style={{ height: 1 }} />

          {isSearching && (
            <div className="load-more-spinner">
              <Loader2 size={24} className="spin-icon" />
              <span>Loading more results…</span>
            </div>
          )}

          {!isSearching && hasMore && (
            <div className="load-more-action">
              <button className="btn btn-secondary" onClick={loadMore}>
                Load more results
              </button>
            </div>
          )}

          {!isSearching && !hasMore && results.length > 0 && (
            <div className="load-more-end">No more results</div>
          )}
        </>
      ) : (
        !isSearching && (
          <div className="empty-state">
            <SearchIcon size={48} />
            <h3>Search for 3D models</h3>
            <p>Results from Thingiverse, Printables, MakerWorld, MyMiniFactory, Cults3D, and MakerOnline will appear here.</p>
          </div>
        )
      )}
    </div>
  );
}
