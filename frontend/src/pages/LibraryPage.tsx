import {
  BookMarked,
  Download,
  ExternalLink,
  Layers,
  Link,
  Loader2,
  Tag,
  Trash2,
  X,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import FilesModal from '../components/FilesModal';
import { useLibraryStore } from '../store/libraryStore';
import type { LibraryModel } from '../types';

const proxyThumb = (url: string) =>
  url ? `/api/sources/proxy-image?url=${encodeURIComponent(url)}` : '';

/* ── Import URL Modal ── */

function ImportURLModal({ onClose }: { onClose: () => void }) {
  const importFromURL = useLibraryStore((s) => s.importFromURL);
  const [url, setUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setSubmitting(true);
    setError('');
    try {
      await importFromURL(url.trim());
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to import');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add from URL</h2>
          <button className="btn-icon" onClick={onClose}><X size={18} /></button>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
          Paste a model URL from Printables, MakerWorld, Thingiverse, Cults3D, or MyMiniFactory.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <input className="input" value={url} onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.printables.com/model/..." autoFocus />
          </div>
          {error && <div style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</div>}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting || !url.trim()}>
              {submitting ? <Loader2 size={14} className="spin-icon" /> : <Link size={14} />} Import
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Tags Modal ── */

function TagsModal({ model, allTags, onClose }: { model: LibraryModel; allTags: string[]; onClose: () => void }) {
  const updateTags = useLibraryStore((s) => s.updateTags);
  const [tags, setTags] = useState<string[]>(model.tags ?? []);
  const [input, setInput] = useState('');
  const [saving, setSaving] = useState(false);

  const addTag = (tag: string) => {
    const t = tag.trim();
    if (t && !tags.includes(t)) setTags((prev) => [...prev, t]);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
      e.preventDefault();
      addTag(input);
    }
    if (e.key === 'Backspace' && !input && tags.length) {
      setTags((prev) => prev.slice(0, -1));
    }
  };

  const save = async () => {
    setSaving(true);
    try { await updateTags(model.id, tags); onClose(); }
    finally { setSaving(false); }
  };

  const suggestions = allTags.filter((t) => !tags.includes(t) && t.toLowerCase().includes(input.toLowerCase()));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ minWidth: 380 }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Tags — {model.name}</h2>
          <button className="btn-icon" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="tag-input-wrap">
          {tags.map((t) => (
            <span key={t} className="tag-chip tag-chip-edit">
              {t}
              <button className="tag-chip-remove" onClick={() => setTags((p) => p.filter((x) => x !== t))}><X size={10} /></button>
            </span>
          ))}
          <input
            className="tag-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={tags.length ? '' : 'Add tags…'}
            autoFocus
            list="dl-tag-suggest"
          />
          {suggestions.length > 0 && (
            <datalist id="dl-tag-suggest">{suggestions.map((s) => <option key={s} value={s} />)}</datalist>
          )}
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8, marginBottom: 16 }}>
          Enter or comma to add · Backspace removes last tag
        </p>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={save} disabled={saving}>
            {saving ? <Loader2 size={14} className="spin-icon" /> : null} Save
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Library Card ── */

function LibraryCard({
  model, allTags, onDelete,
}: {
  model: LibraryModel; allTags: string[]; onDelete: () => void;
}) {
  const { activeTag, setActiveTag } = useLibraryStore();
  const [showTags, setShowTags] = useState(false);
  const [showFiles, setShowFiles] = useState(false);

  return (
    <>
      <div className="card">
        {model.thumbnail_url
          ? <img className="card-image" src={proxyThumb(model.thumbnail_url)} alt={model.name} loading="lazy" />
          : <div className="card-image card-image-placeholder"><Layers size={32} /></div>
        }
        <div className="card-body">
          <div className="card-title" title={model.name}>{model.name}</div>
          <div className="card-meta">
            <span className="card-source">{model.source}</span>
            {model.author && <span>{model.author}</span>}
            {model.in_queue && (
              <span className="card-source" style={{ background: 'var(--accent)', color: '#fff' }}>
                <Layers size={10} /> Queued
              </span>
            )}
          </div>
          <div className="card-tags">
            {(model.tags ?? []).map((tag) => (
              <button
                key={tag}
                className={`tag-chip${activeTag === tag ? ' tag-chip-active' : ''}`}
                onClick={() => setActiveTag(activeTag === tag ? null : tag)}
                title={`Filter by "${tag}"`}
              >
                {tag}
              </button>
            ))}
            <button className="tag-chip tag-chip-add" onClick={() => setShowTags(true)} title="Manage tags">
              <Tag size={10} />
            </button>
          </div>
        </div>
        <div className="card-actions">
          {model.files_count > 0 ? (
            <button className="btn btn-sm btn-primary" onClick={() => setShowFiles(true)} title="Files & Queue">
              <Download size={14} /> {model.files_count} Files
            </button>
          ) : (
            <button className="btn btn-sm btn-secondary" onClick={() => setShowFiles(true)} title="Discover files to queue">
              <Download size={14} /> Files
            </button>
          )}
          <a
            href={model.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-icon"
            title="Open on source site"
            style={{ marginLeft: 'auto' }}
          >
            <ExternalLink size={16} />
          </a>
          <button
            className="btn-icon"
            onClick={onDelete}
            title="Remove from library"
            style={{ color: 'var(--danger)' }}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
      {showTags && <TagsModal model={model} allTags={allTags} onClose={() => setShowTags(false)} />}
      {showFiles && <FilesModal modelId={model.id} modelName={model.name} onClose={() => setShowFiles(false)} />}
    </>
  );
}

/* ── Library Page ── */

export default function LibraryPage() {
  const { models, allTags, activeTag, groupByTag, loading, fetchModels, fetchTags, deleteModel, setActiveTag, setGroupByTag } =
    useLibraryStore();
  const [search, setSearch] = useState('');
  const [showImport, setShowImport] = useState(false);

  useEffect(() => {
    fetchModels({ search: search || undefined, tag: activeTag || undefined });
  }, [search, activeTag, fetchModels]);

  useEffect(() => { fetchTags(); }, [fetchTags]);

  const grouped = useMemo(() => {
    if (!groupByTag) return null;
    const map = new Map<string, LibraryModel[]>();
    const untagged: LibraryModel[] = [];
    for (const m of models) {
      if (!m.tags?.length) { untagged.push(m); continue; }
      for (const t of m.tags) {
        if (!map.has(t)) map.set(t, []);
        map.get(t)!.push(m);
      }
    }
    const entries = Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
    if (untagged.length) entries.push(['Untagged', untagged]);
    return entries;
  }, [groupByTag, models]);

  const renderGrid = (items: LibraryModel[]) => (
    <div className="card-grid">
      {items.map((m) => (
        <LibraryCard key={m.id} model={m} allTags={allTags}
          onDelete={() => deleteModel(m.id)}
        />
      ))}
    </div>
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1>Library</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input className="input" style={{ width: 200 }} placeholder="Filter by name…"
            value={search} onChange={(e) => setSearch(e.target.value)} />
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', userSelect: 'none' }}>
            <label className="toggle">
              <input type="checkbox" checked={groupByTag} onChange={(e) => setGroupByTag(e.target.checked)} />
              <span className="toggle-slider" />
            </label>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Group by tag</span>
          </label>
          <button className="btn btn-primary" onClick={() => setShowImport(true)}>
            <Link size={14} /> Add from URL
          </button>
        </div>
      </div>

      {/* Active tag filter pill */}
      {activeTag && (
        <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tag size={14} style={{ color: 'var(--accent)' }} />
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Tag:</span>
          <span className="tag-chip tag-chip-active">{activeTag}</span>
          <button className="btn-icon" onClick={() => setActiveTag(null)} title="Clear filter"><X size={14} /></button>
        </div>
      )}

      {/* Quick-filter tag bar (when no active tag) */}
      {allTags.length > 0 && !activeTag && !groupByTag && (
        <div className="tag-filter-bar">
          {allTags.map((t) => (
            <button key={t} className="tag-chip" onClick={() => setActiveTag(t)}>{t}</button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="empty-state"><span className="spinner" /></div>
      ) : models.length === 0 ? (
        <div className="empty-state">
          <BookMarked size={48} />
          <h3>Library is empty</h3>
          <p>Search and add models, or import from a URL.</p>
        </div>
      ) : grouped ? (
        grouped.map(([tag, items]) => (
          <div key={tag} className="tag-group">
            <div className="tag-group-header">
              <Tag size={14} /><span>{tag}</span>
              <span className="tag-group-count">{items.length}</span>
            </div>
            {renderGrid(items)}
          </div>
        ))
      ) : (
        renderGrid(models)
      )}

      {showImport && <ImportURLModal onClose={() => setShowImport(false)} />}
    </div>
  );
}
