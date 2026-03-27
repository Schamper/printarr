import { AlertTriangle, CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import { useRef, useState } from 'react';
import type { SourceState } from '../types';

interface Props {
  sources: Record<string, SourceState>;
  isSearching: boolean;
  activeFilter?: Set<string> | null;
  onSourceClick?: (sourceKey: string) => void;
}

export default function SourceProgress({ sources, isSearching, activeFilter, onSourceClick }: Props) {
  const entries = Object.entries(sources);
  const [popupKey, setPopupKey] = useState<string | null>(null);
  const [fadingKey, setFadingKey] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fadeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  if (entries.length === 0 && !isSearching) return null;

  const showPopup = (key: string) => {
    setFadingKey(null);
    setPopupKey(key);
    if (timerRef.current) clearTimeout(timerRef.current);
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
    timerRef.current = setTimeout(() => {
      setFadingKey(key);
      fadeTimerRef.current = setTimeout(() => {
        setPopupKey(null);
        setFadingKey(null);
      }, 300);
    }, 3200);
  };

  return (
    <div className="source-states">
      {entries.map(([key, s]) => {
        const isActive = !!activeFilter?.has(key);
        const unconfigured = s.configured === false;
        return (
          <div key={key} style={{ position: 'relative', display: 'inline-block' }}>
            <div
              className={`source-chip ${s.status}${isActive ? ' source-chip-filtered' : ''}${unconfigured ? ' source-chip-unconfigured' : ''}`}
              onClick={() => unconfigured ? showPopup(key) : onSourceClick?.(key)}
              style={{ cursor: 'pointer' }}
              title={unconfigured ? undefined : isActive ? `Remove ${s.name} from filter` : `Filter by ${s.name}`}
            >
              {unconfigured && <AlertTriangle size={14} />}
              {!unconfigured && s.status === 'searching' && <Loader2 size={14} className="spin-icon" />}
              {!unconfigured && s.status === 'done' && <CheckCircle2 size={14} />}
              {!unconfigured && s.status === 'error' && <XCircle size={14} />}
              {!unconfigured && s.status === 'idle' && <Circle size={14} />}
              <span className="source-chip-name">{s.name}</span>
              {s.resultCount > 0 && (
                <span className="source-chip-count">{s.resultCount}</span>
              )}
              {!unconfigured && s.status === 'error' && (
                <span className="source-chip-error">failed</span>
              )}
            </div>
            {unconfigured && popupKey === key && (
              <div className={`source-chip-popup${fadingKey === key ? ' source-chip-popup-out' : ''}`}>
                <AlertTriangle size={13} />
                {s.name} requires an API key — configure it in Settings
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
