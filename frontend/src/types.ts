export type VideoFormat = 'mp4' | 'mov' | 'avi' | 'MP4' | 'MOV' | 'AVI';

export type PipelineStageId =
  | 'video_uploaded'
  | 'extracting_frames'
  | 'filtering_blurry'
  | 'removing_redundant'
  | 'feature_extraction'
  | 'feature_matching'
  | 'camera_reconstruction'
  | 'dense_reconstruction'
  | 'generating_mesh'
  | 'preparing_model';

export type StageStatus = 'completed' | 'active' | 'pending' | 'failed';

export interface PipelineStageInfo {
  id: PipelineStageId;
  label: string;
  statusText: string;
  status: StageStatus;
}

export type ErrorType =
  | 'unsupported-format'
  | 'upload-failed'
  | 'poor-footage'
  | 'no-usable-frames'
  | 'server-unavailable'
  | 'reconstruction-failed'
  | 'model-loading-failure';

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

export interface ReconstructionJob {
  jobId: string;
  filename: string;
  fileSize: number;
  fileSizeBytesFormatted: string;
  targetOutput?: string;
  currentStageIndex: number;
  currentStageName: string;
  overallStatus: 'processing' | 'completed' | 'failed';
  backendMessage: string;
  glbUrl?: string;
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
