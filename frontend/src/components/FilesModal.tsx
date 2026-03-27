import { Download, RefreshCw, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import * as api from '../api/client';
import { useQueueStore } from '../store/queueStore';
import type { ModelFile } from '../types';

const SLICEABLE = new Set(['stl', 'step', 'stp', 'obj', '3mf', 'amf']);

const SLICERS = [
  { name: 'PrusaSlicer', proto: 'prusaslicer' },
  { name: 'OrcaSlicer',  proto: 'orcaslicer'  },
  { name: 'Bambu Studio', proto: 'bambustudio' },
];

function slicerUrl(proto: string, fileUrl: string) {
  return `${proto}://open?file=${encodeURIComponent(fileUrl)}`;
}

interface Props {
  modelId: number;
  modelName: string;
  onClose: () => void;
}

export default function FilesModal({ modelId, modelName, onClose }: Props) {
  const [files, setFiles] = useState<ModelFile[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [openSlicer, setOpenSlicer] = useState<number | null>(null);
  const [discovering, setDiscovering] = useState(false);

  const queueItems = useQueueStore((s) => s.items);
  const addQueueItem = useQueueStore((s) => s.addItem);
  const [queuedFileIds, setQueuedFileIds] = useState<Set<number>>(() => {
    const ids = new Set<number>();
    for (const qi of queueItems) {
      if (qi.file_id != null) ids.add(qi.file_id);
    }
    return ids;
  });

  const queueFile = async (fileId: number) => {
    await addQueueItem({ file_id: fileId });
    setQueuedFileIds((prev) => new Set([...prev, fileId]));
  };

  useEffect(() => {
    // On first open: load cached files, then auto-discover if none exist yet.
    api.getModelFiles(modelId).then(async (cached) => {
      if (cached.length > 0) {
        setFiles(cached);
        setLoadingFiles(false);
      } else {
        setDiscovering(true);
        setLoadingFiles(false);
        try {
          const discovered = await api.discoverModelFiles(modelId);
          setFiles(discovered);
        } finally {
          setDiscovering(false);
        }
      }
    }).catch(() => setLoadingFiles(false));
  }, []);

  const removeFile = async (fileId: number) => {
    await api.deleteModelFile(modelId, fileId);
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const discoverFiles = async () => {
    setDiscovering(true);
    try {
      const discovered = await api.discoverModelFiles(modelId);
      setFiles(discovered);
    } finally {
      setDiscovering(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ minWidth: 560 }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Files — {modelName}</h2>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <button
              className="btn btn-sm btn-secondary"
              onClick={discoverFiles}
              disabled={discovering}
              title="Auto-discover files from source"
            >
              <RefreshCw size={13} className={discovering ? 'spin-icon' : undefined} />
              {discovering ? 'Scanning…' : 'Discover'}
            </button>
            <button className="btn-icon" onClick={onClose}><X size={18} /></button>
          </div>
        </div>

        {loadingFiles ? (
          <div style={{ textAlign: 'center', padding: 24 }}><span className="spinner" /></div>
        ) : files.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 16 }}>
            No files found. Hit Discover to scan the source.
          </p>
        ) : (
          <div className="files-list">
            {files.map((f) => (
              <div key={f.id} className="file-row">
                <span className="file-type-badge">{f.file_type || '?'}</span>
                <div className="file-info">
                  <span className="file-name">{f.filename}</span>
                </div>
                <div className="file-actions">
                  {SLICEABLE.has(f.file_type?.toLowerCase()) && (
                    <>
                      <button
                        className={`btn btn-sm ${queuedFileIds.has(f.id) ? 'btn-secondary' : 'btn-primary'}`}
                        disabled={queuedFileIds.has(f.id)}
                        onClick={() => queueFile(f.id)}
                        title="Add this file to the print queue"
                      >
                        {queuedFileIds.has(f.id) ? '✓ Queued' : 'Queue'}
                      </button>
                      <div style={{ position: 'relative' }}>
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => setOpenSlicer(openSlicer === f.id ? null : f.id)}
                        >
                          Slice ▾
                        </button>
                        {openSlicer === f.id && (
                          <div className="slicer-dropdown" onClick={(e) => e.stopPropagation()}>
                            {SLICERS.map((s) => (
                              <a
                                key={s.proto}
                                href={slicerUrl(s.proto, f.original_url)}
                                className="slicer-option"
                                onClick={() => setOpenSlicer(null)}
                              >
                                {s.name}
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                  <a
                    href={f.original_url}
                    download={f.filename}
                    className="btn-icon"
                    title="Download"
                  >
                    <Download size={14} />
                  </a>
                  <button className="btn-icon" style={{ color: 'var(--danger)' }} onClick={() => removeFile(f.id)}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 8, display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
