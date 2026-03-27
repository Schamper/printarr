import { Check, Download, ExternalLink, Heart, Plus } from 'lucide-react';
import { useState } from 'react';
import { useLibraryStore } from '../store/libraryStore';
import type { SearchResult } from '../types';

interface Props {
  result: SearchResult;
}

export default function ModelCard({ result }: Props) {
  const addModel = useLibraryStore((s) => s.addModel);
  const [added, setAdded] = useState(result.in_library);
  const [loading, setLoading] = useState(false);

  const [imgError, setImgError] = useState(false);
  const thumbSrc = result.thumbnail_url
    ? `/api/sources/proxy-image?url=${encodeURIComponent(result.thumbnail_url)}`
    : null;

  const handleAdd = async () => {
    if (added || loading) return;
    setLoading(true);
    try {
      await addModel({
        source: result.source,
        source_id: result.source_id,
        url: result.url,
        name: result.name,
        author: result.author,
        description: result.description,
        thumbnail_url: result.thumbnail_url,
        license: result.license,
        download_count: result.download_count,
        like_count: result.like_count,
      });
      setAdded(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      {thumbSrc && !imgError ? (
        <img
          className="card-image"
          src={thumbSrc}
          alt={result.name}
          loading="lazy"
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="card-image" />
      )}
      <div className="card-body">
        <div className="card-title" title={result.name}>
          {result.name}
        </div>
        <div className="card-meta">
          <span className="card-source">{result.source}</span>
          {result.author && <span>{result.author}</span>}
        </div>
        <div className="card-meta" style={{ marginTop: 6 }}>
          {result.like_count > 0 && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <Heart size={12} /> {result.like_count}
            </span>
          )}
          {result.download_count > 0 && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <Download size={12} /> {result.download_count}
            </span>
          )}
        </div>
      </div>
      <div className="card-actions">
        <button
          className={`btn btn-sm ${added ? 'btn-secondary' : 'btn-primary'}`}
          onClick={handleAdd}
          disabled={added || loading}
        >
          {added ? <Check size={14} /> : <Plus size={14} />}
          {added ? 'In Library' : 'Add'}
        </button>
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-sm btn-secondary"
        >
          <ExternalLink size={14} />
          Open
        </a>
      </div>
    </div>
  );
}
