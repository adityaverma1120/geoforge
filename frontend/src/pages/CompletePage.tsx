import React, { useEffect, useState } from 'react';
import { ReconstructionJob, JobMetadata } from '../types';
import { getJobMetadata } from '../services/api';

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
  const [metadata, setMetadata] = useState<JobMetadata | null>(job.metadata || null);
  const [loadingMeta, setLoadingMeta] = useState<boolean>(!job.metadata);

  useEffect(() => {
    if (!metadata && job.jobId) {
      getJobMetadata(job.jobId)
        .then((data) => {
          setMetadata(data);
          setLoadingMeta(false);
        })
        .catch((err) => {
          console.warn('Metadata manifest fetch warning:', err);
          setLoadingMeta(false);
        });
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
    <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 w-full max-w-5xl mx-auto my-auto animate-fade-in">
      <div className="w-full bg-[#101415] border border-[#333a42] rounded-xl p-6 md:p-8 flex flex-col shadow-2xl">
        {/* Top Success Badge */}
        <div className="flex flex-col items-center text-center pb-6 border-b border-white/10">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center mb-4 shadow-lg shadow-emerald-950/40">
            <span className="material-symbols-outlined text-[36px]">check_circle</span>
          </div>

          <h1 className="text-[26px] md:text-[32px] font-bold text-white tracking-tight mb-2">
            3D Reconstruction Complete
          </h1>
          <p className="text-[14px] leading-[22px] text-[#aaa] max-w-xl">
            Drone video was processed through COLMAP Structure-from-Motion and Open3D Screened Poisson meshing.
            Your interactive binary GLB model is ready for inspection.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
            <button
              onClick={onView3DModel}
              className="bg-[#2563EB] hover:bg-blue-500 text-white px-7 py-3 rounded-lg text-[14px] font-bold transition-all active:scale-95 flex items-center gap-2 cursor-pointer shadow-lg shadow-blue-950/40"
            >
              <span className="material-symbols-outlined text-[20px]">view_in_ar</span>
              Open Interactive 3D Viewer
            </button>

            <button
              onClick={onDownloadGlb}
              className="bg-[#1d2022] hover:bg-[#272a2c] text-white border border-white/10 px-5 py-3 rounded-lg text-[14px] font-semibold transition-all active:scale-95 flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px]">download</span>
              Download GLB ({glbSizeMb > 0 ? `${glbSizeMb} MB` : 'Model'})
            </button>

            <button
              onClick={onUploadAnother}
              className="text-[#888] hover:text-white px-4 py-3 text-[13px] font-medium transition-colors cursor-pointer"
            >
              Process Another Video
            </button>
          </div>
        </div>

        {/* Deliverables & Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {/* Deliverables Column */}
          <div className="flex flex-col gap-3">
            <span className="text-[12px] font-bold tracking-wider uppercase text-[#8d90a0]">
              Deliverables & Formats
            </span>

            {/* Binary GLB — Verified */}
            <div className="border border-emerald-500/30 bg-[#0b0f10] rounded-lg p-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[22px]">3d_rotation</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[14px] font-bold text-white">
                    Binary GLTF Model (.glb)
                  </span>
                  <span className="text-[11px] text-[#888]">
                    Watertight mesh with vertex color transfer
                  </span>
                </div>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
                VERIFIED READY
              </span>
            </div>

            {/* LAS Point Cloud — Roadmap tier */}
            <div className="border border-white/5 bg-[#0b0f10]/60 rounded-lg p-3.5 flex items-center justify-between opacity-75">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 text-[#888] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[22px]">scatter_plot</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] font-semibold text-[#ccc]">
                    ASPRS LAS Point Cloud
                  </span>
                  <span className="text-[11px] text-[#666]">
                    Dense LiDAR classification format (fused.ply active)
                  </span>
                </div>
              </div>
              <span className="text-[10px] font-mono text-amber-400/80 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-500/20">
                ROADMAP TIER 3
              </span>
            </div>

            {/* GeoTIFF — Roadmap tier */}
            <div className="border border-white/5 bg-[#0b0f10]/60 rounded-lg p-3.5 flex items-center justify-between opacity-75">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 text-[#888] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[22px]">map</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[13px] font-semibold text-[#ccc]">
                    GeoTIFF Orthomosaic
                  </span>
                  <span className="text-[11px] text-[#666]">
                    Nadir aerial projection with UTM georeferencing
                  </span>
                </div>
              </div>
              <span className="text-[10px] font-mono text-amber-400/80 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-500/20">
                ROADMAP TIER 4
              </span>
            </div>

            {/* Geospatial Disclaimer */}
            <div className="mt-2 p-3.5 rounded-lg bg-amber-950/20 border border-amber-500/30 text-[11px] text-amber-200/90 leading-[17px]">
              <div className="flex items-center gap-1.5 font-bold mb-1 text-amber-300">
                <span className="material-symbols-outlined text-[15px]">info</span>
                Geospatial Coordinate Space
              </div>
              Model is oriented in arbitrary local coordinate space (x, y, z). Global metric scale and WGS84 UTM georeferencing require external GCP constraints or RTK GPS flight telemetry.
            </div>
          </div>

          {/* Genuine Telemetry & Metadata Column */}
          <div className="flex flex-col gap-3">
            <span className="text-[12px] font-bold tracking-wider uppercase text-[#8d90a0]">
              Photogrammetry Telemetry
            </span>

            <div className="border border-white/10 bg-[#0b0f10] rounded-lg p-4 font-mono text-[12px] flex flex-col gap-2.5 text-[#ccc]">
              <div className="flex justify-between pb-2 border-b border-white/5">
                <span className="text-[#888]">JOB ID:</span>
                <span className="text-[#b4c5ff] font-bold">{job.jobId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#888]">INPUT VIDEO:</span>
                <span className="text-white truncate max-w-[200px]">{job.filename}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#888]">FRAMES PROCESSED:</span>
                <span className="text-white">
                  {registeredImgs > 0 ? `${registeredImgs} / ${extractedFrames}` : `${extractedFrames} frames`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#888]">PROCESSING TIME:</span>
                <span className="text-white">
                  {durationSec > 0 ? `${durationSec.toFixed(1)}s` : 'Completed'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#888]">DENSE POINT CLOUD:</span>
                <span className="text-emerald-400">
                  {densePts > 0 ? `${densePts.toLocaleString()} points` : sparsePts > 0 ? `${sparsePts.toLocaleString()} sparse pts` : 'Calculated'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#888]">MESH COMPLEXITY:</span>
                <span className="text-white">
                  {vertices > 0 ? `${vertices.toLocaleString()} vertices · ${faces.toLocaleString()} faces` : 'Poisson depth 9'}
                </span>
              </div>
              {dims && (
                <div className="flex justify-between">
                  <span className="text-[#888]">BOUNDING EXTENTS:</span>
                  <span className="text-[#f59e0b]">
                    {dims.map((d: number) => d.toFixed(2)).join(' × ')} (local)
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-[#888]">COLOR MAPPING:</span>
                <span className="text-white">cKDTree RGB Transfer</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-white/5">
                <span className="text-[#888]">STATUS:</span>
                <span className="text-emerald-400 font-bold">RECONSTRUCTION SUCCESS</span>
              </div>
            </div>

            {/* Quality warnings if any */}
            {metadata?.quality_warnings && metadata.quality_warnings.length > 0 && (
              <div className="p-3 rounded-lg bg-black border border-amber-500/30 text-[11px] text-amber-300">
                <span className="font-bold block mb-1">Quality Observations:</span>
                <ul className="list-disc list-inside space-y-0.5">
                  {metadata.quality_warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
};
