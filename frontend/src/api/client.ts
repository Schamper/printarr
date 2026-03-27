import type { IndexerConfig, LibraryModel, ModelFile, QueueItem, SourceInfo } from '../types';

const BASE = '/api';

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

// -- Library --

export async function getLibrary(params?: {
  search?: string;
  tag?: string;
}): Promise<LibraryModel[]> {
  const sp = new URLSearchParams();
  if (params?.search) sp.set('search', params.search);
  if (params?.tag) sp.set('tag', params.tag);
  const qs = sp.toString();
  return fetchJSON(`${BASE}/library${qs ? '?' + qs : ''}`);
}

export async function addToLibrary(data: Partial<LibraryModel>): Promise<LibraryModel> {
  return fetchJSON(`${BASE}/library`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function importFromURL(url: string): Promise<LibraryModel> {
  return fetchJSON(`${BASE}/library/import-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
}

export async function updateLibraryTags(id: number, tags: string[]): Promise<LibraryModel> {
  return fetchJSON(`${BASE}/library/${id}/tags`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tags }),
  });
}

export async function getAllTags(): Promise<string[]> {
  return fetchJSON(`${BASE}/library/tags`);
}

export async function deleteLibraryModel(id: number): Promise<void> {
  await fetch(`${BASE}/library/${id}`, { method: 'DELETE' });
}

// -- Files --

export async function getModelFiles(modelId: number): Promise<ModelFile[]> {
  return fetchJSON(`${BASE}/library/${modelId}/files`);
}

export async function deleteModelFile(modelId: number, fileId: number): Promise<void> {
  await fetch(`${BASE}/library/${modelId}/files/${fileId}`, { method: 'DELETE' });
}

export async function discoverModelFiles(modelId: number): Promise<ModelFile[]> {
  return fetchJSON(`${BASE}/library/${modelId}/discover-files`, { method: 'POST' });
}

// -- Queue --

export async function getQueue(): Promise<QueueItem[]> {
  return fetchJSON(`${BASE}/queue`);
}

export async function addToQueue(data: {
  file_id: number;
  notes?: string;
  filament_type?: string;
  filament_color?: string;
  copies?: number;
}): Promise<QueueItem> {
  return fetchJSON(`${BASE}/queue`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function updateQueueItem(
  id: number,
  data: Partial<QueueItem>,
): Promise<QueueItem> {
  return fetchJSON(`${BASE}/queue/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function removeFromQueue(id: number): Promise<void> {
  await fetch(`${BASE}/queue/${id}`, { method: 'DELETE' });
}

export async function reorderQueue(
  items: Array<{ id: number; sort_order: number }>,
): Promise<void> {
  await fetch(`${BASE}/queue/reorder`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(items),
  });
}

// -- Settings --

export async function getIndexers(): Promise<IndexerConfig[]> {
  return fetchJSON(`${BASE}/settings/indexers`);
}

export async function updateIndexer(
  name: string,
  data: { enabled?: boolean; api_key?: string },
): Promise<IndexerConfig> {
  return fetchJSON(`${BASE}/settings/indexers/${encodeURIComponent(name)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function getSettings(): Promise<Array<{ key: string; value: string }>> {
  return fetchJSON(`${BASE}/settings`);
}

export async function updateSetting(key: string, value: string): Promise<void> {
  await fetch(`${BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, value }),
  });
}

// -- Sources --

export async function getSources(): Promise<SourceInfo[]> {
  return fetchJSON(`${BASE}/sources`);
}
