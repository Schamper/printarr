import { Download, ExternalLink, GripVertical, Layers, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueueStore } from '../store/queueStore';
import type { QueueItem } from '../types';

const FILAMENT_TYPES = ['PLA', 'PETG', 'ABS', 'TPU', 'ASA', 'Nylon', 'PC', 'PVA', 'HIPS', 'Resin'];

const SLICERS = [
  { name: 'PrusaSlicer', proto: 'prusaslicer' },
  { name: 'OrcaSlicer',  proto: 'orcaslicer'  },
  { name: 'Bambu Studio', proto: 'bambustudio' },
];

function slicerUrl(proto: string, fileUrl: string) {
  return `${proto}://open?file=${encodeURIComponent(fileUrl)}`;
}

const proxyThumb = (url: string) =>
  url ? `/api/sources/proxy-image?url=${encodeURIComponent(url)}` : '';

/* ── Inline editable cell ── */

function EditableCell({
  value,
  placeholder,
  onSave,
  multiline,
  datalist,
}: {
  value: string;
  placeholder: string;
  onSave: (v: string) => void;
  multiline?: boolean;
  datalist?: string[];
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const ref = useRef<HTMLTextAreaElement | HTMLInputElement>(null);

  useEffect(() => {
    if (editing) ref.current?.focus();
  }, [editing]);

  const commit = () => {
    setEditing(false);
    if (draft !== value) onSave(draft);
  };

  if (!editing) {
    return (
      <span
        className="editable-cell"
        onClick={() => { setDraft(value); setEditing(true); }}
        title="Click to edit"
      >
        {value || <span className="editable-placeholder">{placeholder}</span>}
      </span>
    );
  }

  if (multiline) {
    return (
      <textarea
        ref={ref as React.RefObject<HTMLTextAreaElement>}
        className="input editable-input"
        value={draft}
        rows={2}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Escape') { setDraft(value); setEditing(false); }
        }}
      />
    );
  }

  const listId = datalist ? `dl-${placeholder}` : undefined;
  return (
    <>
      <input
        ref={ref as React.RefObject<HTMLInputElement>}
        className="input editable-input"
        value={draft}
        list={listId}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') commit();
          if (e.key === 'Escape') { setDraft(value); setEditing(false); }
        }}
      />
      {datalist && (
        <datalist id={listId}>
          {datalist.map((d) => <option key={d} value={d} />)}
        </datalist>
      )}
    </>
  );
}

/* ── Queue Page ── */

export default function QueuePage() {
  const { items, loading, fetchItems, updateItem, removeItem, reorderItems } = useQueueStore();
  const [openSlicer, setOpenSlicer] = useState<number | null>(null);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  /* ── Drag‑to‑reorder state ── */
  const dragIdx = useRef<number | null>(null);
  const [overIdx, setOverIdx] = useState<number | null>(null);

  const onDragStart = useCallback((e: React.DragEvent, idx: number) => {
    dragIdx.current = idx;
    e.dataTransfer.effectAllowed = 'move';
    const row = (e.target as HTMLElement).closest('tr');
    if (row) e.dataTransfer.setDragImage(row, 0, 0);
  }, []);

  const onDragOver = useCallback((e: React.DragEvent, idx: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setOverIdx(idx);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent, dropIdx: number) => {
      e.preventDefault();
      setOverIdx(null);
      const from = dragIdx.current;
      dragIdx.current = null;
      if (from === null || from === dropIdx) return;

      const ids = items.map((i) => i.id);
      const [moved] = ids.splice(from, 1);
      ids.splice(dropIdx, 0, moved);
      reorderItems(ids);
    },
    [items, reorderItems],
  );

  const onDragEnd = useCallback(() => {
    dragIdx.current = null;
    setOverIdx(null);
  }, []);

  const saveField = (item: QueueItem, field: string, value: string | number) => {
    updateItem(item.id, { [field]: value });
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Print Queue</h1>
      </div>

      {loading ? (
        <div className="empty-state"><span className="spinner" /></div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <Layers size={48} />
          <h3>Queue is empty</h3>
          <p>Go to your library and queue models for printing.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: 32 }}></th>
                <th style={{ width: 50 }}></th>
                <th>File</th>
                <th>Model</th>
                <th>Copies</th>
                <th>Filament</th>
                <th>Notes</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => (
                <tr
                  key={item.id}
                  draggable
                  onDragStart={(e) => onDragStart(e, idx)}
                  onDragOver={(e) => onDragOver(e, idx)}
                  onDrop={(e) => onDrop(e, idx)}
                  onDragEnd={onDragEnd}
                  className={overIdx === idx ? 'drop-target' : ''}
                >
                  <td className="drag-handle">
                    <GripVertical size={16} />
                  </td>
                  <td>
                    {item.model_thumbnail_url && (
                      <img
                        src={proxyThumb(item.model_thumbnail_url)}
                        alt=""
                        loading="lazy"
                        style={{ width: 40, height: 40, borderRadius: 4, objectFit: 'cover' }}
                      />
                    )}
                  </td>
                  <td>
                    <div style={{ fontWeight: 500 }}>
                      {item.file_filename || item.model_name}
                    </div>
                    {item.file_filename && item.file_file_type && (
                      <span className="file-type-badge" style={{ marginTop: 2 }}>{item.file_file_type}</span>
                    )}
                  </td>
                  <td>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{item.model_name}</div>
                    <span className="card-source">{item.model_source}</span>
                  </td>
                  <td>
                    <input
                      className="input"
                      type="number"
                      min={1}
                      value={item.copies}
                      onChange={(e) => saveField(item, 'copies', Math.max(1, parseInt(e.target.value) || 1))}
                      style={{ width: 60, padding: '4px 8px', fontSize: 12 }}
                    />
                  </td>
                  <td style={{ minWidth: 160 }}>
                    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                      <EditableCell
                        value={item.filament_type}
                        placeholder="Type"
                        datalist={FILAMENT_TYPES}
                        onSave={(v) => saveField(item, 'filament_type', v)}
                      />
                      {(item.filament_type || item.filament_color) && <span style={{ color: 'var(--text-muted)' }}>/</span>}
                      <EditableCell
                        value={item.filament_color}
                        placeholder="Color"
                        onSave={(v) => saveField(item, 'filament_color', v)}
                      />
                    </div>
                  </td>
                  <td style={{ maxWidth: 250 }}>
                    <EditableCell
                      value={item.notes}
                      placeholder="Add notes..."
                      multiline
                      onSave={(v) => saveField(item, 'notes', v)}
                    />
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                      {item.file_original_url && (
                        <div style={{ position: 'relative' }}>
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => setOpenSlicer(openSlicer === item.id ? null : item.id)}
                          >
                            Slice ▾
                          </button>
                          {openSlicer === item.id && (
                            <div className="slicer-dropdown" onClick={(e) => e.stopPropagation()}>
                              {SLICERS.map((s) => (
                                <a
                                  key={s.proto}
                                  href={slicerUrl(s.proto, item.file_original_url)}
                                  className="slicer-option"
                                  onClick={() => setOpenSlicer(null)}
                                >
                                  {s.name}
                                </a>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                      {item.file_original_url && (
                        <a
                          href={item.file_original_url}
                          download={item.file_filename || true}
                          className="btn-icon"
                          title="Download file"
                        >
                          <Download size={16} />
                        </a>
                      )}
                      <a href={item.model_url} target="_blank" rel="noopener noreferrer" className="btn-icon" title="Open model page">
                        <ExternalLink size={16} />
                      </a>
                      <button className="btn-icon" title="Remove from queue" onClick={() => removeItem(item.id)} style={{ color: 'var(--danger)' }}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
