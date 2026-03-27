export interface SearchResult {
  source: string;
  source_id: string;
  name: string;
  url: string;
  author: string;
  thumbnail_url: string;
  description: string;
  license: string;
  download_count: number;
  like_count: number;
  published_at: string;
  in_library: boolean;
}

export interface LibraryModel {
  id: number;
  source: string;
  source_id: string;
  url: string;
  name: string;
  author: string;
  description: string;
  thumbnail_url: string;
  license: string;
  download_count: number;
  like_count: number;
  tags: string[];
  added_at: string;
  updated_at: string;
  in_queue: boolean;
  files_count: number;
}

export interface ModelFile {
  id: number;
  library_model_id: number;
  filename: string;
  original_url: string;
  file_type: string;
  size_bytes: number;
  added_at: string;
}

export interface QueueItem {
  id: number;
  library_model_id: number;
  file_id: number | null;
  notes: string;
  filament_type: string;
  filament_color: string;
  copies: number;
  sort_order: number;
  added_at: string;
  model_name: string;
  model_source: string;
  model_url: string;
  model_author: string;
  model_thumbnail_url: string;
  file_filename: string;
  file_original_url: string;
  file_file_type: string;
}

export interface IndexerConfig {
  id: number;
  name: string;
  display_name: string;
  enabled: boolean;
  has_api_key: boolean;
  priority: number;
  requires_api_key: boolean;
  api_key_label: string;
}

export interface SourceInfo {
  name: string;
  display_name: string;
  base_url: string;
}

export interface SourceState {
  name: string;
  status: 'idle' | 'searching' | 'done' | 'error';
  resultCount: number;
  configured: boolean;
}
