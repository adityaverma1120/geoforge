import React, { useEffect, useState } from 'react';
import { PipelineStageId, ReconstructionJob } from '../types';

interface ProcessingPageProps {
  job: ReconstructionJob;
  onCancel: () => void;
  onRetry: () => void;
  onUploadDifferent: () => void;
  onViewResult: () => void;
}

export const PIPELINE_STAGES: {
  id: PipelineStageId;
  label: string;
  description: string;
  backendMatches: string[];
}[] = [
  {
    id: 'validating_video',
    label: '1. Video validation',
    description: 'Container readability, FourCC codec, resolution & visual integrity checks',
    backendMatches: ['validating_video', 'uploading', 'video_uploaded', 'queued'],
  },
  {
    id: 'extracting_frames',
    label: '2. Frame extraction',
    description: 'OpenCV frame extraction at adaptive 2.0 FPS key intervals',
    backendMatches: ['extracting_frames'],
  },
  {
    id: 'filtering_frames',
    label: '3. Image filtering',
    description: 'Laplacian variance blur, luminance, contrast & redundancy reduction',
    backendMatches: ['filtering_frames', 'redundancy_filter', 'filtering_blurry', 'removing_redundant'],
  },
  {
    id: 'extracting_features',
    label: '4. Feature extraction',
    description: 'COLMAP CUDA SIFT keypoint detection (~3,500 points/frame)',
    backendMatches: ['extracting_features', 'feature_extraction'],
  },
  {
    id: 'matching_features',
    label: '5. Feature matching',
    description: 'Sequential matching with loop detection & geometric verification',
    backendMatches: ['matching_features', 'feature_matching'],
  },
  {
    id: 'sparse_reconstruction',
    label: '6. Sparse reconstruction',
    description: 'Incremental SfM, camera pose estimation & bundle adjustment',
    backendMatches: ['sparse_reconstruction', 'sparse_quality_check', 'camera_reconstruction'],
  },
  {
    id: 'dense_reconstruction',
    label: '7. Dense reconstruction',
    description: 'COLMAP CUDA PatchMatch multi-view stereo & fused point cloud generation',
    backendMatches: ['image_undistortion', 'dense_stereo', 'stereo_fusion', 'dense_reconstruction'],
  },
  {
    id: 'processing_pointcloud',
    label: '8. Point cloud processing',
    description: 'Open3D statistical outlier removal and 3D bounding box computation',
    backendMatches: ['processing_pointcloud', 'point_cloud_cleaning'],
  },
  {
    id: 'generating_mesh',
    label: '9. Mesh generation',
    description: 'Open3D Screened Poisson Surface Reconstruction (Depth 9, 7% trim)',
    backendMatches: ['generating_mesh', 'poisson_meshing'],
  },
  {
    id: 'generating_texture',
    label: '10. Texture generation',
    description: 'Spatial cKDTree nearest-neighbor RGB color transfer & material binding',
    backendMatches: ['generating_texture', 'texture_mapping'],
  },
  {
    id: 'exporting_glb',
    label: '11. GLB export',
    description: 'Trimesh PBR serialization to binary glTF v2 (.glb)',
    backendMatches: ['exporting_glb'],
  },
  {
    id: 'validating_model',
    label: '12. Model validation',
    description: 'Binary header magic verification and accuracy metadata generation',
    backendMatches: ['validating_model', 'completed', 'complete'],
  },
];

export const ProcessingPage: React.FC<ProcessingPageProps> = ({
  job,
  onCancel,
  onRetry,
  onUploadDifferent,
  onViewResult,
}) => {
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  useEffect(() => {
    // Stop counter if job is in a terminal state
    const isTerminal = ['completed', 'complete', 'failed', 'cancelled'].includes(job.overallStatus);
    if (isTerminal) return;

    const timer = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [job.overallStatus]);

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  const getStageStatus = (index: number): 'completed' | 'active' | 'pending' | 'failed' => {
    if (['failed', 'cancelled'].includes(job.overallStatus) && index === job.currentStageIndex) {
      return 'failed';
    }
    if (index < job.currentStageIndex) {
      return 'completed';
    }
    if (index === job.currentStageIndex) {
      return ['completed', 'complete'].includes(job.overallStatus) ? 'completed' : 'active';
    }
    return 'pending';
  };

  const currentPercent = Math.min(100, Math.max(0, job.progressPercent ?? Math.round(((job.currentStageIndex + 1) / 12) * 100)));

  return (
    <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 w-full max-w-4xl mx-auto my-auto animate-fade-in">
      <div className="w-full bg-[#101415] border border-[#333a42] rounded-xl p-6 md:p-8 flex flex-col shadow-2xl">
        {/* Top Header Card */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-white/10 pb-6 mb-6">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-[11px] font-mono text-[#b4c5ff] bg-[#1d2022] px-2.5 py-1 rounded border border-white/10">
                JOB: {job.jobId}
              </span>
              <span className="text-[11px] font-mono text-[#8d90a0] bg-black/40 px-2 py-1 rounded border border-white/5">
                ELAPSED: {formatTime(secondsElapsed)}
              </span>
              <span
                className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold ${
                  ['completed', 'complete'].includes(job.overallStatus)
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : job.overallStatus === 'failed'
                    ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                    : job.overallStatus === 'cancelled'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                    : 'bg-blue-500/20 text-blue-400 border border-blue-500/40 animate-pulse'
                }`}
              >
                {job.overallStatus}
              </span>
            </div>
            <h1 className="text-[22px] md:text-[26px] font-bold text-white tracking-tight">
              {['completed', 'complete'].includes(job.overallStatus)
                ? 'Photogrammetric Reconstruction Complete'
                : job.overallStatus === 'failed'
                ? 'Reconstruction Pipeline Halted'
                : job.overallStatus === 'cancelled'
                ? 'Reconstruction Cancelled'
                : 'Reconstruction Pipeline Active'}
            </h1>
            <p className="text-[13px] text-[#888] mt-0.5">
              Source video: <span className="font-mono text-white">{job.filename}</span> ({job.fileSizeBytesFormatted})
            </p>
          </div>

          {/* Action Button */}
          <div>
            {['completed', 'complete'].includes(job.overallStatus) ? (
              <button
                onClick={onViewResult}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-lg text-[13px] font-bold transition-all active:scale-95 flex items-center gap-2 cursor-pointer shadow-lg shadow-emerald-950/40"
              >
                <span className="material-symbols-outlined text-[18px]">view_in_ar</span>
                View 3D Model
              </button>
            ) : ['failed', 'cancelled'].includes(job.overallStatus) ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={onRetry}
                  className="bg-[#2563EB] hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-[12px] font-semibold transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[16px]">refresh</span>
                  Retry Job
                </button>
                <button
                  onClick={onUploadDifferent}
                  className="bg-[#1d2022] hover:bg-[#272a2c] text-white border border-white/10 px-4 py-2 rounded-lg text-[12px] font-semibold transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  New Video
                </button>
              </div>
            ) : (
              <button
                onClick={onCancel}
                className="text-[#aaa] hover:text-red-400 border border-white/10 hover:border-red-500/40 px-3.5 py-1.5 rounded-lg text-[12px] font-medium transition-colors flex items-center gap-1.5 cursor-pointer bg-white/[0.02]"
              >
                <span className="material-symbols-outlined text-[16px]">cancel</span>
                Cancel Job
              </button>
            )}
          </div>
        </div>

        {/* Real Progress Bar */}
        <div className="mb-6 p-4 rounded-xl bg-black/40 border border-white/5">
          <div className="flex justify-between items-center text-[12px] font-mono mb-2">
            <span className="text-[#aaa]">
              STAGE {Math.min(job.currentStageIndex + 1, 12)} OF 12: {PIPELINE_STAGES[job.currentStageIndex]?.label || 'Processing'}
            </span>
            <span className="text-[#f59e0b] font-bold">{currentPercent}%</span>
          </div>
          <div className="h-2.5 rounded-full overflow-hidden bg-white/10">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${currentPercent}%`,
                background: ['completed', 'complete'].includes(job.overallStatus)
                  ? '#10b981'
                  : job.overallStatus === 'failed'
                  ? '#ef4444'
                  : 'linear-gradient(90deg, #f59e0b, #3b82f6)',
              }}
            />
          </div>
        </div>

        {/* 12 Backend Pipeline Stages List */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center text-[11px] font-mono text-[#8d90a0] px-1 mb-1">
            <span>PHOTOGRAMMETRY ENGINE STAGES (COLMAP + OPEN3D + TRIMESH)</span>
            <span>STATUS</span>
          </div>

          <div className="grid grid-cols-1 gap-2">
            {PIPELINE_STAGES.map((stage, idx) => {
              const status = getStageStatus(idx);

              return (
                <div
                  key={stage.id}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                    status === 'active'
                      ? 'bg-[#1d2022] border-[#f59e0b] shadow-md'
                      : status === 'completed'
                      ? 'bg-[#0b0f10]/80 border-white/5'
                      : status === 'failed'
                      ? 'bg-red-950/30 border-red-500/40'
                      : 'bg-[#0b0f10]/40 border-white/5 opacity-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {/* Stage icon indicator */}
                    <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0">
                      {status === 'completed' && (
                        <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center">
                          <span className="material-symbols-outlined text-[15px]">check</span>
                        </div>
                      )}
                      {status === 'active' && (
                        <div className="w-6 h-6 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b] flex items-center justify-center animate-pulse">
                          <span className="text-[12px] font-bold">●</span>
                        </div>
                      )}
                      {status === 'pending' && (
                        <div className="w-6 h-6 rounded-full bg-[#1d2022] text-[#555] border border-white/10 flex items-center justify-center">
                          <span className="text-[12px]">○</span>
                        </div>
                      )}
                      {status === 'failed' && (
                        <div className="w-6 h-6 rounded-full bg-red-900 text-red-200 border border-red-500 flex items-center justify-center font-bold text-[12px]">
                          !
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col">
                      <span
                        className={`text-[13px] font-semibold leading-tight ${
                          status === 'active'
                            ? 'text-[#fbbf24]'
                            : status === 'completed'
                            ? 'text-white'
                            : status === 'failed'
                            ? 'text-red-300'
                            : 'text-[#666]'
                        }`}
                      >
                        {stage.label}
                      </span>
                      <span className="text-[11px] text-[#777] hidden sm:block mt-0.5">
                        {stage.description}
                      </span>
                    </div>
                  </div>

                  {/* Stage status badge */}
                  <div className="text-right shrink-0">
                    {status === 'completed' && (
                      <span className="text-[10px] font-mono text-emerald-400 uppercase bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
                        Passed
                      </span>
                    )}
                    {status === 'active' && (
                      <span className="text-[10px] font-mono text-[#fbbf24] uppercase bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/30 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b] animate-ping"></span>
                        Active
                      </span>
                    )}
                    {status === 'pending' && (
                      <span className="text-[10px] font-mono text-[#555] uppercase">
                        Queued
                      </span>
                    )}
                    {status === 'failed' && (
                      <span className="text-[10px] font-mono text-red-400 uppercase bg-red-950/40 px-2 py-0.5 rounded border border-red-500/30">
                        Failed
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Backend Telemetry HUD */}
        <div className="mt-6 p-4 rounded-xl bg-black border border-white/10 font-mono text-[12px]">
          <div className="flex justify-between items-center mb-2 pb-2 border-b border-white/10 text-[11px]">
            <span className="flex items-center gap-1.5 text-white font-semibold">
              <span className="material-symbols-outlined text-[16px] text-[#b4c5ff]">terminal</span>
              LIVE BACKEND ENGINE LOG
            </span>
            <span className="text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              FASTAPI & SQLite LINKED
            </span>
          </div>
          <div className="flex flex-col gap-1 text-[11px]">
            <p className="text-[#666]">
              &gt; Workspace: backend/temp/{job.jobId}
            </p>
            <p className="text-[#888]">
              &gt; Processing stage: {PIPELINE_STAGES[job.currentStageIndex]?.label || 'Active'}
            </p>
            {job.backendMessage && (
              <p className="text-[#b4c5ff] font-medium mt-1">
                &gt; {job.backendMessage}
              </p>
            )}
            {job.error?.message && (
              <p className="text-red-400 font-medium mt-1">
                &gt; Error: {job.error.message}
              </p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
};
