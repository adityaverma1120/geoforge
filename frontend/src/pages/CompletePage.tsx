import React from 'react';
import { ReconstructionJob } from '../types';

interface CompletePageProps {
  job: ReconstructionJob;
  onView3DModel: () => void;
  onDownloadGlb: () => void;
  onUploadAnother: () => void;
  onNavigate: (route: string) => void;
}

export const CompletePage: React.FC<CompletePageProps> = ({
  job,
  onView3DModel,
  onDownloadGlb,
  onUploadAnother,
  onNavigate,
}) => {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-6 w-full max-w-4xl mx-auto my-auto animate-fade-in">
      <div className="w-full bg-[#101415] border border-[#434655] rounded-xl p-6 md:p-8 flex flex-col shadow-2xl">
        {/* Top Success Badge */}
        <div className="flex flex-col items-center text-center pb-6 border-b border-[#1E293B]">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-[#34d399] border border-[#34d399]/40 flex items-center justify-center mb-4 shadow-lg shadow-emerald-950/40">
            <span className="material-symbols-outlined text-[36px]">check_circle</span>
          </div>

          <h1 className="text-[26px] md:text-[30px] font-bold text-[#e0e3e5] tracking-tight mb-2">
            3D Reconstruction Complete
          </h1>
          <p className="text-[14px] leading-[22px] text-[#c3c6d7] max-w-lg">
            Your drone video has been converted into an interactive geospatial 3D mesh model and dense point cloud.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
            <button
              onClick={onView3DModel}
              className="bg-[#2563EB] hover:bg-blue-600 text-white px-7 py-3 rounded text-[14px] font-medium leading-[20px] active:scale-95 transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-blue-950/40"
            >
              <span className="material-symbols-outlined text-[20px]">view_in_ar</span>
              Open Interactive 3D Viewer
            </button>

            <button
              onClick={onDownloadGlb}
              className="bg-[#1d2022] hover:bg-[#272a2c] text-[#e0e3e5] border border-[#434655] px-5 py-3 rounded text-[14px] font-medium leading-[20px] active:scale-95 transition-all flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px]">download</span>
              Download GLB Asset
            </button>
          </div>
        </div>

        {/* Output Assets & Job Summary Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {/* Generated Artifacts */}
          <div className="flex flex-col gap-3">
            <span className="text-[12px] font-bold tracking-wider uppercase text-[#8d90a0]">
              Generated 3D Deliverables
            </span>

            <div className="border border-[#1E293B] bg-[#0b0f10] rounded-lg p-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded bg-[#101415] border border-[#2563EB] text-[#b4c5ff] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">3d_rotation</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] font-semibold text-[#e0e3e5]">
                    Interactive GLB Model
                  </span>
                  <span className="text-[11px] text-[#8d90a0]">Optimized for WebGL & AR</span>
                </div>
              </div>
              <span className="text-[11px] font-mono text-[#34d399] bg-[#34d399]/10 px-2 py-0.5 rounded border border-[#34d399]/30">
                READY
              </span>
            </div>

            <div className="border border-[#1E293B] bg-[#0b0f10] rounded-lg p-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded bg-[#101415] border border-[#434655] text-[#b4c5ff] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">scatter_plot</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] font-semibold text-[#e0e3e5]">
                    Dense Point Cloud (LAS)
                  </span>
                  <span className="text-[11px] text-[#8d90a0]">High-density LiDAR classification</span>
                </div>
              </div>
              <span className="text-[11px] font-mono text-[#34d399] bg-[#34d399]/10 px-2 py-0.5 rounded border border-[#34d399]/30">
                READY
              </span>
            </div>

            <div className="border border-[#1E293B] bg-[#0b0f10] rounded-lg p-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded bg-[#101415] border border-[#434655] text-[#b4c5ff] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">map</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] font-semibold text-[#e0e3e5]">
                    Orthomosaic GeoTIFF
                  </span>
                  <span className="text-[11px] text-[#8d90a0]">Georeferenced 2D aerial mosaic</span>
                </div>
              </div>
              <span className="text-[11px] font-mono text-[#34d399] bg-[#34d399]/10 px-2 py-0.5 rounded border border-[#34d399]/30">
                READY
              </span>
            </div>
          </div>

          {/* Reconstruction Job Metrics */}
          <div className="flex flex-col gap-3">
            <span className="text-[12px] font-bold tracking-wider uppercase text-[#8d90a0]">
              Job Telemetry & Metadata
            </span>

            <div className="border border-[#1E293B] bg-[#0b0f10] rounded-lg p-4 font-mono text-[12px] flex flex-col gap-2.5 text-[#c3c6d7]">
              <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
                <span className="text-[#8d90a0]">JOB_IDENTIFIER:</span>
                <span className="text-[#b4c5ff]">{job.jobId}</span>
              </div>
              <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
                <span className="text-[#8d90a0]">SOURCE_FOOTAGE:</span>
                <span className="text-[#e0e3e5] truncate max-w-[180px]">{job.filename}</span>
              </div>
              <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
                <span className="text-[#8d90a0]">FOOTAGE_SIZE:</span>
                <span className="text-[#e0e3e5]">{job.fileSizeBytesFormatted}</span>
              </div>
              <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
                <span className="text-[#8d90a0]">PIPELINE_ENGINE:</span>
                <span className="text-[#34d399]">10/10 Stages Verified</span>
              </div>
              <div className="flex justify-between pt-0.5">
                <span className="text-[#8d90a0]">COORDINATE_SYS:</span>
                <span className="text-[#e0e3e5]">WGS 84 / Local Mesh</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="mt-8 pt-6 border-t border-[#1E293B] flex justify-between items-center">
          <button
            onClick={() => onNavigate('home')}
            className="text-[13px] text-[#8d90a0] hover:text-[#e0e3e5] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">home</span>
            Return to Home
          </button>

          <button
            onClick={onUploadAnother}
            className="text-[13px] text-[#b4c5ff] hover:underline flex items-center gap-1.5 cursor-pointer font-medium"
          >
            <span className="material-symbols-outlined text-[16px]">add_circle</span>
            Reconstruct Another Video
          </button>
        </div>
      </div>
    </main>
  );
};
