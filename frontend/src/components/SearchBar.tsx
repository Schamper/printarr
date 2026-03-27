import { Search } from 'lucide-react';
import { useState, type FormEvent } from 'react';

interface Props {
  onSearch: (query: string) => void;
  isSearching: boolean;
  initialQuery?: string;
}

export default function SearchBar({ onSearch, isSearching, initialQuery = '' }: Props) {
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) onSearch(trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className="input-group" style={{ maxWidth: 600 }}>
      <input
        className="input"
        type="text"
        placeholder="Search 3D models across all sources..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button className="btn btn-primary" type="submit" disabled={isSearching}>
        {isSearching ? <span className="spinner" /> : <Search size={16} />}
        Search
      </button>
    </form>
  );
}
