import React, { useEffect, useState } from 'react';
import { ReconstructionJob, JobMetadata } from '../types';
import { ThreeDViewer } from '../components/ThreeDViewer';
import { getJobMetadata } from '../services/api';

interface ResultPageProps {
  job: ReconstructionJob;
  onNewReconstruction: () => void;
  onDownloadGlb: () => void;
  onModelLoadError: (error: Error) => void;
  onNavigate: (route: string) => void;
}

export const ResultPage: React.FC<ResultPageProps> = ({
  job,
  onNewReconstruction,
  onDownloadGlb,
  onModelLoadError,
  onNavigate,
}) => {
  const [activeTab, setActiveTab] = useState<'info' | 'telemetry' | 'controls'>('info');
  const [metadata, setMetadata] = useState<JobMetadata | null>(job.metadata || null);

  useEffect(() => {
    if (!metadata && job.jobId) {
      getJobMetadata(job.jobId)
        .then((data) => setMetadata(data))
        .catch((err) => console.warn('Metadata fetch warning:', err));
    }
  }, [job.jobId, metadata]);

  const durationSec = metadata?.processing_duration_seconds ?? 0;
  const densePts = metadata?.photogrammetry_stats?.dense_points ?? 0;
  const sparsePts = metadata?.photogrammetry_stats?.sparse_points ?? 0;
  const vertices = metadata?.mesh_stats?.vertices ?? 0;
  const faces = metadata?.mesh_stats?.faces ?? 0;
  const registeredImgs = metadata?.photogrammetry_stats?.registered_images ?? 0;
  const extractedFrames = metadata?.filtering_stats?.extracted_frames ?? 0;
  const glbSizeMb = metadata?.model_deliverable?.file_size_mb ?? 0;
  const dims = metadata?.mesh_stats?.bounding_dimensions || metadata?.photogrammetry_stats?.bounding_box?.dimensions;

  return (
    <div className="flex-1 flex flex-col w-full h-[calc(100vh-56px)] bg-[#020617] overflow-hidden">
      {/* Sub-header Navigation Bar */}
      <div className="w-full h-14 bg-[#101415] border-b border-[#333a42] px-4 md:px-6 flex items-center justify-between z-20 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('complete')}
            className="text-[#8d90a0] hover:text-white p-1.5 rounded transition-colors flex items-center gap-1 text-[12px] font-medium cursor-pointer"
            title="Back to Summary"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            <span className="hidden sm:inline">Summary</span>
          </button>
          <div className="h-4 w-[1px] bg-white/10"></div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[14px] font-semibold text-white truncate max-w-[200px] sm:max-w-md">
                {job.filename}
              </span>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30 hidden sm:inline">
                3D WEBGL MODEL
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onDownloadGlb}
            className="bg-[#2563EB] hover:bg-blue-500 text-white px-4 py-1.5 rounded-lg text-[12px] font-bold active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span>Download GLB</span>
            {glbSizeMb > 0 && <span className="hidden sm:inline opacity-75">({glbSizeMb} MB)</span>}
          </button>

          <button
            onClick={onNewReconstruction}
            className="bg-[#1d2022] hover:bg-[#272a2c] text-white border border-white/10 px-3.5 py-1.5 rounded-lg text-[12px] font-medium active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
            <span className="hidden md:inline">New Video</span>
          </button>
        </div>
      </div>

      {/* Main 3D Canvas Area with Collapsible Sidebar */}
      <div className="flex-1 flex flex-col md:flex-row relative w-full h-full overflow-hidden">
        {/* 3D WebGL Canvas Viewport */}
        <div className="flex-1 relative w-full h-full bg-[#020617]">
          <ThreeDViewer
            modelUrl={job.glbUrl}
            onModelLoadError={onModelLoadError}
            className="w-full h-full"
          />
        </div>

        {/* Right Model Inspector Drawer */}
        <div className="w-full md:w-80 h-auto md:h-full bg-[#101415] border-t md:border-t-0 md:border-l border-[#333a42] flex flex-col shrink-0 z-10">
          {/* Tabs */}
          <div className="flex border-b border-white/10 bg-[#0b0f10] text-[12px] font-medium text-[#8d90a0]">
            <button
              onClick={() => setActiveTab('info')}
              className={`flex-1 py-2.5 text-center transition-colors cursor-pointer ${
                activeTab === 'info'
                  ? 'text-[#b4c5ff] border-b-2 border-[#2563EB] bg-[#101415] font-semibold'
                  : 'hover:text-white'
              }`}
            >
              Model Info
            </button>
            <button
              onClick={() => setActiveTab('telemetry')}
              className={`flex-1 py-2.5 text-center transition-colors cursor-pointer ${
                activeTab === 'telemetry'
                  ? 'text-[#b4c5ff] border-b-2 border-[#2563EB] bg-[#101415] font-semibold'
                  : 'hover:text-white'
              }`}
            >
              Telemetry
            </button>
            <button
              onClick={() => setActiveTab('controls')}
              className={`flex-1 py-2.5 text-center transition-colors cursor-pointer ${
                activeTab === 'controls'
                  ? 'text-[#b4c5ff] border-b-2 border-[#2563EB] bg-[#101415] font-semibold'
                  : 'hover:text-white'
              }`}
            >
              Navigation
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-4 flex-1 overflow-y-auto font-mono text-[12px] text-[#ccc] space-y-4">
            {activeTab === 'info' && (
              <div className="space-y-3">
                <div className="bg-[#0b0f10] p-3 rounded-lg border border-white/10 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-[#888]">JOB ID:</span>
                    <span className="text-[#b4c5ff] truncate max-w-[150px]">{job.jobId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">FORMAT:</span>
                    <span className="text-white">glTF v2.0 (.glb)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">POINTS:</span>
                    <span className="text-emerald-400">
                      {densePts > 0 ? `${densePts.toLocaleString()} pts` : sparsePts > 0 ? `${sparsePts.toLocaleString()} pts` : 'Calculated'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">VERTICES:</span>
                    <span className="text-white">
                      {vertices > 0 ? vertices.toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">FACES:</span>
                    <span className="text-white">
                      {faces > 0 ? faces.toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  {dims && (
                    <div className="flex justify-between">
                      <span className="text-[#888]">EXTENTS:</span>
                      <span className="text-[#f59e0b]">
                        {dims.map((d: number) => d.toFixed(1)).join(' × ')}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-[#888]">MATERIAL:</span>
                    <span className="text-white">PBR (cKDTree RGB)</span>
                  </div>
                </div>

                <div className="bg-amber-950/20 p-3 rounded-lg border border-amber-500/20 text-[11px] text-amber-200/90 leading-relaxed font-sans">
                  <div className="font-bold text-amber-300 mb-1 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">public</span>
                    Arbitrary Coordinates
                  </div>
                  Model is scaled and oriented in local metric coordinates. For true geographic elevation (WGS84) or survey RTK accuracy, Ground Control Points (GCPs) are required.
                </div>
              </div>
            )}

            {activeTab === 'telemetry' && (
              <div className="space-y-3">
                <div className="bg-[#0b0f10] p-3 rounded-lg border border-white/10 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-[#888]">PIPELINE:</span>
                    <span className="text-emerald-400">COLMAP + Open3D</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">PROCESSING:</span>
                    <span className="text-white">{durationSec > 0 ? `${durationSec.toFixed(1)}s` : 'Done'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">REGISTERED:</span>
                    <span className="text-white">
                      {registeredImgs > 0 ? `${registeredImgs} / ${extractedFrames} frames` : `${extractedFrames} frames`}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">SURFACE MESH:</span>
                    <span className="text-white">Screened Poisson</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#888]">DENSITY TRIM:</span>
                    <span className="text-white">7.0% Low-density</span>
                  </div>
                </div>

                {metadata?.quality_warnings && metadata.quality_warnings.length > 0 && (
                  <div className="bg-black p-3 rounded-lg border border-white/10 text-[11px] space-y-1">
                    <span className="text-amber-400 font-bold block">Observations:</span>
                    {metadata.quality_warnings.map((w, i) => (
                      <p key={i} className="text-[#aaa]">&gt; {w}</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'controls' && (
              <div className="space-y-3 font-sans">
                <div className="bg-[#0b0f10] p-3 rounded-lg border border-white/10 space-y-2 text-[12px]">
                  <span className="text-[#8d90a0] block text-[11px] uppercase font-bold font-mono">
                    Mouse & Trackpad Controls
                  </span>
                  <div className="text-[12px] text-[#aaa] space-y-2">
                    <div className="flex items-start gap-2">
                      <span className="text-white font-semibold w-24 shrink-0">Left Click:</span>
                      <span>Orbit / Rotate 3D terrain</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-white font-semibold w-24 shrink-0">Right Click:</span>
                      <span>Pan camera laterally</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-white font-semibold w-24 shrink-0">Scroll Wheel:</span>
                      <span>Zoom camera in & out</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-white font-semibold w-24 shrink-0">Toolbar:</span>
                      <span>Reset view, toggle grid, fullscreen</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
