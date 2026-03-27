import { useEffect, useState } from 'react';
import * as api from '../api/client';
import type { IndexerConfig } from '../types';

export default function SettingsPage() {
  const [indexers, setIndexers] = useState<IndexerConfig[]>([]);

  useEffect(() => {
    api.getIndexers().then(setIndexers);
  }, []);

  const toggleIndexer = async (name: string, enabled: boolean) => {
    const updated = await api.updateIndexer(name, { enabled });
    setIndexers((prev) => prev.map((i) => (i.name === name ? updated : i)));
  };

  const KEY_PLACEHOLDER = '••••••••';

  const updateApiKey = async (name: string, value: string) => {
    if (value === KEY_PLACEHOLDER) return;
    const updated = await api.updateIndexer(name, { api_key: value });
    setIndexers((prev) => prev.map((i) => (i.name === name ? updated : i)));
  };

  const hasAnyApiKey = indexers.some((i) => i.requires_api_key);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      <div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>
          Enable or disable model sources. Sources marked with an API key field require one to function.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Enabled</th>
                {hasAnyApiKey && <th>API Key</th>}
              </tr>
            </thead>
            <tbody>
              {indexers.map((idx) => (
                <tr key={idx.name}>
                  <td style={{ fontWeight: 500 }}>{idx.display_name || idx.name}</td>
                  <td>
                    <label className="toggle">
                      <input
                        type="checkbox"
                        checked={idx.enabled}
                        onChange={(e) => toggleIndexer(idx.name, e.target.checked)}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </td>
                  {hasAnyApiKey && (
                    <td>
                      {idx.requires_api_key ? (
                        <input
                          className="input"
                          style={{ width: 280 }}
                          type="password"
                          placeholder={idx.api_key_label}
                          defaultValue={idx.has_api_key ? KEY_PLACEHOLDER : ''}
                          onBlur={(e) => updateApiKey(idx.name, e.target.value)}
                        />
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>No key required</span>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
