import React, { useState } from 'react';
import { ReconstructionJob } from '../types';
import { ThreeDViewer } from '../components/ThreeDViewer';

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
  const [activeTab, setActiveTab] = useState<'info' | 'layers' | 'camera'>('info');

  return (
    <div className="flex-1 flex flex-col w-full h-[calc(100vh-56px)] bg-[#020617] overflow-hidden">
      {/* Sub-header Navigation Bar */}
      <div className="w-full h-14 bg-[#101415] border-b border-[#434655] px-4 md:px-6 flex items-center justify-between z-20 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('complete')}
            className="text-[#8d90a0] hover:text-[#e0e3e5] p-1.5 rounded transition-colors flex items-center gap-1 text-[12px] font-medium"
            title="Back to Summary"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            <span className="hidden sm:inline">Summary</span>
          </button>
          <div className="h-4 w-[1px] bg-[#434655]"></div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[14px] font-semibold text-[#e0e3e5] truncate max-w-[200px] sm:max-w-md">
                {job.filename}
              </span>
              <span className="text-[10px] font-mono text-[#34d399] bg-[#34d399]/10 px-2 py-0.5 rounded border border-[#34d399]/30 hidden sm:inline">
                3D MODEL LOADED
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onDownloadGlb}
            className="bg-[#2563EB] hover:bg-blue-600 text-white px-3.5 py-1.5 rounded text-[12px] font-medium leading-[16px] active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span className="hidden sm:inline">Download</span> GLB
          </button>

          <button
            onClick={onNewReconstruction}
            className="bg-[#1d2022] hover:bg-[#272a2c] text-[#e0e3e5] border border-[#434655] px-3.5 py-1.5 rounded text-[12px] font-medium leading-[16px] active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
            <span className="hidden md:inline">New</span> Reconstruction
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
        <div className="w-full md:w-80 h-auto md:h-full bg-[#101415] border-t md:border-t-0 md:border-l border-[#434655] flex flex-col shrink-0 z-10">
          {/* Tabs */}
          <div className="flex border-b border-[#434655] bg-[#0b0f10] text-[12px] font-medium text-[#8d90a0]">
            <button
              onClick={() => setActiveTab('info')}
              className={`flex-1 py-2.5 text-center transition-colors cursor-pointer ${
                activeTab === 'info'
                  ? 'text-[#b4c5ff] border-b-2 border-[#2563EB] bg-[#101415]'
                  : 'hover:text-[#e0e3e5]'
              }`}
            >
              Model Info
            </button>
            <button
              onClick={() => setActiveTab('layers')}
              className={`flex-1 py-2.5 text-center transition-colors cursor-pointer ${
                activeTab === 'layers'
                  ? 'text-[#b4c5ff] border-b-2 border-[#2563EB] bg-[#101415]'
                  : 'hover:text-[#e0e3e5]'
              }`}
            >
              Layers
            </button>
            <button
              onClick={() => setActiveTab('camera')}
              className={`flex-1 py-2.5 text-center transition-colors cursor-pointer ${
                activeTab === 'camera'
                  ? 'text-[#b4c5ff] border-b-2 border-[#2563EB] bg-[#101415]'
                  : 'hover:text-[#e0e3e5]'
              }`}
            >
              Telemetry
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-4 flex-1 overflow-y-auto font-mono text-[12px] text-[#c3c6d7] space-y-4">
            {activeTab === 'info' && (
              <div className="space-y-3">
                <div className="bg-[#0b0f10] p-3 rounded border border-[#1E293B] space-y-2">
                  <div className="flex justify-between">
                    <span className="text-[#8d90a0]">JOB_ID:</span>
                    <span className="text-[#b4c5ff]">{job.jobId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8d90a0]">FORMAT:</span>
                    <span className="text-[#e0e3e5]">glTF Binary (.glb)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8d90a0]">POINT_COUNT:</span>
                    <span className="text-[#34d399]">12,000+ Points</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8d90a0]">PRECISION:</span>
                    <span className="text-[#e0e3e5]">High Photogrammetry</span>
                  </div>
                </div>

                <div className="bg-[#0b0f10] p-3 rounded border border-[#1E293B] space-y-2">
                  <span className="text-[#8d90a0] block text-[11px] uppercase font-bold">
                    Viewport Navigation
                  </span>
                  <div className="text-[11px] text-[#8d90a0] space-y-1">
                    <p>• Left Click + Drag: Orbit / Rotate</p>
                    <p>• Right Click / Two Fingers: Pan View</p>
                    <p>• Scroll Wheel / Pinch: Zoom</p>
                    <p>• Toolbar Icons: Camera Reset & Fullscreen</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'layers' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2.5 bg-[#0b0f10] rounded border border-[#1E293B]">
                  <span className="text-[#e0e3e5]">Dense Point Cloud</span>
                  <span className="material-symbols-outlined text-[18px] text-[#34d399]">
                    visibility
                  </span>
                </div>
                <div className="flex items-center justify-between p-2.5 bg-[#0b0f10] rounded border border-[#1E293B]">
                  <span className="text-[#e0e3e5]">Reconstructed Wireframe</span>
                  <span className="material-symbols-outlined text-[18px] text-[#34d399]">
                    visibility
                  </span>
                </div>
                <div className="flex items-center justify-between p-2.5 bg-[#0b0f10] rounded border border-[#1E293B]">
                  <span className="text-[#e0e3e5]">CAD Ground Plane Grid</span>
                  <span className="material-symbols-outlined text-[18px] text-[#34d399]">
                    visibility
                  </span>
                </div>
              </div>
            )}

            {activeTab === 'camera' && (
              <div className="space-y-2 text-[11px]">
                <div className="bg-[#0b0f10] p-3 rounded border border-[#1E293B] space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-[#8d90a0]">RENDERER:</span>
                    <span className="text-[#e0e3e5]">Three.js WebGL</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8d90a0]">TONE_MAPPING:</span>
                    <span className="text-[#e0e3e5]">ACESFilmic</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8d90a0]">SHADER_COLOR:</span>
                    <span className="text-[#34d399]">Elevation-Ramp</span>
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
