export type VideoFormat = 'mp4' | 'mov' | 'avi' | 'mkv' | 'MP4' | 'MOV' | 'AVI' | 'MKV';

export type PipelineStageId =
  | 'validating_video'
  | 'extracting_frames'
  | 'filtering_frames'
  | 'redundancy_filter'
  | 'extracting_features'
  | 'matching_features'
  | 'sparse_reconstruction'
  | 'dense_reconstruction'
  | 'processing_pointcloud'
  | 'generating_mesh'
  | 'generating_texture'
  | 'exporting_glb'
  | 'validating_model'
  | 'completed';

export type StageStatus = 'completed' | 'active' | 'pending' | 'failed';

export interface PipelineStageInfo {
  id: PipelineStageId;
  label: string;
  description: string;
  backendStageNames: string[];
}

export type ErrorType =
  | 'unsupported-format'
  | 'file-too-large'
  | 'upload-failed'
  | 'poor-footage'
  | 'no-usable-frames'
  | 'server-unavailable'
  | 'reconstruction-failed'
  | 'model-loading-failure'
  | 'job-cancelled';

export interface ErrorDetails {
  type: ErrorType;
  title: string;
  message: string;
  suggestedActions?: string[];
  diagnostics?: {
    code?: string;
    timestamp?: string;
    server?: string;
    filename?: string;
    mimeType?: string;
    details?: string;
    trace?: string;
  };
}

export interface JobMetadata {
  job_id: string;
  filename: string;
  created_at?: string;
  completed_at?: string;
  processing_duration_seconds?: number;
  source_video?: {
    filename?: string;
    resolution?: string;
    width?: number;
    height?: number;
    fps?: number;
    duration_seconds?: number;
    total_frames?: number;
    codec?: string;
    file_size_mb?: number;
  };
  filtering_stats?: {
    extracted_frames?: number;
    sharp_frames_kept?: number;
    blurry_frames_removed?: number;
    brightness_frames_removed?: number;
    contrast_frames_removed?: number;
    redundant_frames_removed?: number;
    final_frames_for_colmap?: number;
  };
  photogrammetry_stats?: {
    registered_images?: number;
    registration_ratio?: number;
    num_cameras?: number;
    sparse_points?: number;
    dense_points?: number;
    cleaned_points?: number;
    outliers_removed?: number;
    bounding_box?: {
      dimensions?: [number, number, number];
      min_bound?: [number, number, number];
      max_bound?: [number, number, number];
    };
  };
  mesh_stats?: {
    vertices?: number;
    faces?: number;
    bounding_dimensions?: [number, number, number];
  };
  model_deliverable?: {
    format?: string;
    file_path?: string;
    file_size_mb?: number;
    magic?: string;
    version?: number;
    download_url?: string;
    model_url?: string;
  };
  quality_warnings?: string[];
  geospatial_notes?: string;
}

export interface ReconstructionJob {
  jobId: string;
  filename: string;
  fileSize: number;
  fileSizeBytesFormatted: string;
  currentStageIndex: number;
  currentStageName: string;
  overallStatus: 'queued' | 'processing' | 'completed' | 'complete' | 'failed' | 'cancelled';
  progressPercent?: number;
  backendMessage: string;
  glbUrl?: string;
  downloadUrl?: string;
  metadata?: JobMetadata;
  meshObjReady?: boolean;
  pointCloudLasReady?: boolean;
  orthomosaicTiffReady?: boolean;
  coordinateSystem?: string;
  processingQuality?: string;
  error?: ErrorDetails;
}

export interface UploadResponse {
  job_id?: string;
  id?: string;
  status?: string;
  message?: string;
  glb_url?: string;
  model_url?: string;
  [key: string]: unknown;
}

export interface JobHistoryItem {
  id: string;
  job_id?: string;
  filename: string;
  status: 'queued' | 'processing' | 'complete' | 'completed' | 'failed' | 'cancelled';
  stage?: string;
  progress_percent?: number;
  stage_message?: string;
  created_at: string;
  updated_at?: string;
  model_path?: string;
  result?: {
    model_url?: string;
    download_url?: string;
    metadata_url?: string;
    glb_size_mb?: number;
    frames_extracted?: number;
    frames_used?: number;
    num_sparse_points?: number;
    warnings?: string[];
    [key: string]: unknown;
  };
}
