import React, { useEffect, useState } from 'react';
import { PipelineStageId, PipelineStageInfo, ReconstructionJob } from '../types';

interface ProcessingPageProps {
  job: ReconstructionJob;
  onCancel: () => void;
  onRetry: () => void;
  onUploadDifferent: () => void;
  onViewResult: () => void;
}

export const PIPELINE_STAGES: { id: PipelineStageId; label: string; description: string }[] = [
  { id: 'video_uploaded', label: 'Video uploaded', description: 'Uploaded payload verified by node' },
  { id: 'extracting_frames', label: 'Extracting frames', description: 'Decompressing video stream at key intervals' },
  { id: 'filtering_blurry', label: 'Filtering blurry frames', description: 'Variance of Laplacian motion blur analysis' },
  { id: 'removing_redundant', label: 'Removing redundant frames', description: 'Cosine image similarity thresholding' },
  { id: 'feature_extraction', label: 'Feature extraction', description: 'SIFT/ORB detector keypoint identification' },
  { id: 'feature_matching', label: 'Feature matching', description: 'FLANN nearest-neighbor geometric consistency' },
  { id: 'camera_reconstruction', label: 'Camera reconstruction', description: 'Structure from Motion (SfM) bundle adjustment' },
  { id: 'dense_reconstruction', label: 'Dense reconstruction', description: 'Multi-View Stereo (MVS) depth map fusion' },
  { id: 'generating_mesh', label: 'Generating mesh', description: 'Poisson surface reconstruction & UV unwrapping' },
  { id: 'preparing_model', label: 'Preparing 3D model', description: 'GLB compression & WebGL asset packaging' },
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
    const timer = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  const getStageStatus = (index: number): 'completed' | 'active' | 'pending' | 'failed' => {
    if (job.overallStatus === 'failed' && index === job.currentStageIndex) {
      return 'failed';
    }
    if (index < job.currentStageIndex) {
      return 'completed';
    }
    if (index === job.currentStageIndex) {
      return job.overallStatus === 'completed' ? 'completed' : 'active';
    }
    return 'pending';
  };

  return (
    <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-6 w-full max-w-4xl mx-auto my-auto animate-fade-in">
      <div className="w-full bg-[#101415] border border-[#434655] rounded-xl p-6 md:p-8 flex flex-col shadow-2xl">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#1E293B] pb-6 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[12px] font-mono text-[#b4c5ff] bg-[#1d2022] px-2.5 py-1 rounded border border-[#434655]">
                JOB: {job.jobId}
              </span>
              <span className="text-[12px] font-mono text-[#8d90a0]">
                ELAPSED: {formatTime(secondsElapsed)}
              </span>
            </div>
            <h1 className="text-[22px] md:text-[26px] font-bold text-[#e0e3e5] tracking-tight">
              {job.overallStatus === 'completed'
                ? 'Reconstruction Complete'
                : job.overallStatus === 'failed'
                ? '3D Reconstruction Failed'
                : 'Reconstruction in Progress'}
            </h1>
            <p className="text-[13px] text-[#c3c6d7] mt-0.5">
              Source file: <span className="font-mono text-[#e0e3e5]">{job.filename}</span> ({job.fileSizeBytesFormatted})
            </p>
          </div>

          {/* Top Right Action Badge */}
          <div>
            {job.overallStatus === 'completed' ? (
              <button
                onClick={onViewResult}
                className="bg-[#10b981] hover:bg-emerald-600 text-white px-5 py-2.5 rounded text-[13px] font-medium leading-[20px] active:scale-95 transition-all flex items-center gap-2 cursor-pointer shadow-lg"
              >
                <span className="material-symbols-outlined text-[18px]">view_in_ar</span>
                View 3D Model
              </button>
            ) : job.overallStatus === 'failed' ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={onRetry}
                  className="bg-[#2563EB] text-white px-4 py-2 rounded text-[12px] font-medium hover:bg-blue-600 transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[16px]">refresh</span>
                  Retry
                </button>
                <button
                  onClick={onUploadDifferent}
                  className="bg-[#1d2022] text-[#e0e3e5] border border-[#434655] px-4 py-2 rounded text-[12px] font-medium hover:bg-[#272a2c] transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  New Video
                </button>
              </div>
            ) : (
              <button
                onClick={onCancel}
                className="text-[#8d90a0] hover:text-[#ffb4ab] border border-[#434655] hover:border-[#ffb4ab]/30 px-3.5 py-1.5 rounded text-[12px] font-medium transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px]">cancel</span>
                Cancel Process
              </button>
            )}
          </div>
        </div>

        {/* 10 Real Pipeline Stages List */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center text-[12px] font-mono text-[#8d90a0] px-2 mb-1">
            <span>PIPELINE STAGE EXECUTION (10-STEP ENGINE)</span>
            <span>
              STAGE {Math.min(job.currentStageIndex + 1, 10)} OF 10
            </span>
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            {PIPELINE_STAGES.map((stage, idx) => {
              const status = getStageStatus(idx);

              return (
                <div
                  key={stage.id}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                    status === 'active'
                      ? 'bg-[#1d2022] border-[#f59e0b] shadow-md'
                      : status === 'completed'
                      ? 'bg-[#0b0f10]/80 border-[#1E293B]'
                      : status === 'failed'
                      ? 'bg-[#93000a]/20 border-[#ffb4ab]/50'
                      : 'bg-[#0b0f10]/40 border-[#1E293B]/60 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {/* Stage Indicator: Completed = ✓, Active = ●, Pending = ○, Failed = ! */}
                    <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0">
                      {status === 'completed' && (
                        <div className="w-7 h-7 rounded-full bg-emerald-500/20 text-[#34d399] border border-[#34d399]/40 flex items-center justify-center">
                          <span className="material-symbols-outlined text-[18px]">check</span>
                        </div>
                      )}
                      {status === 'active' && (
                        <div className="w-7 h-7 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b] flex items-center justify-center animate-pulse-amber">
                          <span className="text-[14px] leading-none font-bold">●</span>
                        </div>
                      )}
                      {status === 'pending' && (
                        <div className="w-7 h-7 rounded-full bg-[#1d2022] text-[#8d90a0] border border-[#434655] flex items-center justify-center">
                          <span className="text-[14px] leading-none">○</span>
                        </div>
                      )}
                      {status === 'failed' && (
                        <div className="w-7 h-7 rounded-full bg-[#93000a] text-[#ffb4ab] border border-[#ffb4ab] flex items-center justify-center">
                          <span className="text-[14px] leading-none font-bold">!</span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono text-[#8d90a0]">
                          {(idx + 1).toString().padStart(2, '0')}
                        </span>
                        <span
                          className={`text-[14px] font-medium leading-[20px] ${
                            status === 'active'
                              ? 'text-[#fbbf24] font-semibold'
                              : status === 'completed'
                              ? 'text-[#e0e3e5]'
                              : status === 'failed'
                              ? 'text-[#ffb4ab]'
                              : 'text-[#8d90a0]'
                          }`}
                        >
                          {stage.label}
                        </span>
                      </div>
                      <span className="text-[11px] text-[#8d90a0] hidden sm:block">
                        {stage.description}
                      </span>
                    </div>
                  </div>

                  {/* Right Status Badge */}
                  <div className="text-right">
                    {status === 'completed' && (
                      <span className="text-[11px] font-mono text-[#34d399] uppercase">
                        Completed
                      </span>
                    )}
                    {status === 'active' && (
                      <span className="text-[11px] font-mono text-[#fbbf24] uppercase flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b] animate-ping"></span>
                        Processing
                      </span>
                    )}
                    {status === 'pending' && (
                      <span className="text-[11px] font-mono text-[#64748b] uppercase">
                        Queued
                      </span>
                    )}
                    {status === 'failed' && (
                      <span className="text-[11px] font-mono text-[#ffb4ab] uppercase">
                        Halted
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Technical Logs HUD */}
        <div className="mt-6 p-4 rounded-lg bg-[#0b0f10] border border-[#1E293B] font-mono text-[12px] text-[#8d90a0]">
          <div className="flex justify-between items-center mb-2 pb-2 border-b border-[#1E293B]">
            <span className="flex items-center gap-1.5 text-[#c3c6d7]">
              <span className="material-symbols-outlined text-[16px] text-[#b4c5ff]">terminal</span>
              LIVE PIPELINE TELEMETRY
            </span>
            <span className="text-[#34d399]">FASTAPI NODE ACTIVE</span>
          </div>
          <div className="flex flex-col gap-1 text-[11px] text-[#c3c6d7]">
            <p className="text-[#8d90a0]">
              &gt; Initialized photogrammetric worker for file: {job.filename}
            </p>
            <p className="text-[#8d90a0]">
              &gt; Current pipeline task: {PIPELINE_STAGES[job.currentStageIndex]?.label || 'Processing'}
            </p>
            {job.backendMessage && (
              <p className="text-[#b4c5ff] font-medium">
                &gt; {job.backendMessage}
              </p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
};
