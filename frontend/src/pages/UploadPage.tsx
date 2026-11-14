import React, { useRef, useState, useEffect } from 'react';

interface UploadPageProps {
  onStartReconstruction: (file: File) => void;
  onUnsupportedFormat: (file: File) => void;
  onNavigate: (route: string) => void;
  isUploading?: boolean;
  uploadProgress?: number;
}

const MAX_FILE_SIZE_BYTES = 4 * 1024 * 1024 * 1024; // 4 GiB
const ALLOWED_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv'];

export const UploadPage: React.FC<UploadPageProps> = ({
  onStartReconstruction,
  onUnsupportedFormat,
  onNavigate,
  isUploading = false,
  uploadProgress = 0,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [videoDimensions, setVideoDimensions] = useState<{ width: number; height: number; duration: number } | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Clean up object URL when component unmounts or file changes
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);

    // Empty file check
    if (file.size === 0) {
      setValidationError('The selected file is empty (0 bytes). Please select a valid drone video.');
      return;
    }

    // Size check
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setValidationError(
        `File size (${(file.size / (1024 * 1024 * 1024)).toFixed(2)} GB) exceeds the maximum upload limit of 4.0 GB.`
      );
      return;
    }

    // Extension check
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
      setValidationError(
        `Unsupported video format ".${ext || 'unknown'}". Supported formats are MP4, MOV, AVI, and MKV.`
      );
      onUnsupportedFormat(file);
      return;
    }

    // Revoke previous URL
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }

    // Generate preview for browser-playable containers
    if (['mp4', 'mov'].includes(ext)) {
      try {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } catch (e) {
        console.warn('Could not create video preview URL:', e);
      }
    } else {
      setPreviewUrl(null);
    }

    setSelectedFile(file);
    setVideoDimensions(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleRemoveFile = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setSelectedFile(null);
    setVideoDimensions(null);
    setValidationError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const handleStart = () => {
    if (selectedFile && !isUploading) {
      onStartReconstruction(selectedFile);
    }
  };

  const handleLoadedMetadata = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    const video = e.currentTarget;
    setVideoDimensions({
      width: video.videoWidth,
      height: video.videoHeight,
      duration: Math.round(video.duration),
    });
  };

  return (
    <main
      className="flex-1 flex flex-col items-center justify-center p-5 md:p-10 w-full max-w-3xl mx-auto my-auto"
      style={{ minHeight: 'calc(100vh - 56px)' }}
    >
      {/* Back link */}
      <div className="w-full mb-6">
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-1.5 text-[12px] font-mono transition-colors cursor-pointer text-[#666] hover:text-white"
        >
          <span className="material-symbols-outlined text-[15px]">arrow_back</span>
          Back to Home
        </button>
      </div>

      {/* Title */}
      <div className="w-full mb-6">
        <h1 className="text-[28px] md:text-[34px] font-black text-white leading-tight mb-2">
          Upload Flight Video
        </h1>
        <p className="text-[14px] leading-[22px] text-[#888]">
          Single-pass continuous drone or phone video conversion to textured 3D WebGL model (.glb).
        </p>
      </div>

      {/* Validation Error Banner */}
      {validationError && (
        <div className="w-full mb-6 p-4 rounded-xl bg-red-950/40 border border-red-500/40 flex items-start gap-3">
          <span className="material-symbols-outlined text-red-400 text-[20px] shrink-0 mt-0.5">error</span>
          <div className="flex-1">
            <h4 className="text-[13px] font-semibold text-red-200">Validation Error</h4>
            <p className="text-[12px] text-red-300/90 mt-0.5">{validationError}</p>
          </div>
          <button
            onClick={() => setValidationError(null)}
            className="text-red-400 hover:text-red-200 text-[12px] p-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Hidden input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".mp4,.mov,.avi,.mkv,video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
        onChange={handleFileChange}
        className="hidden"
        id="drone-video-file-input"
      />

      {/* Drop zone */}
      {!selectedFile ? (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setIsDragOver(false);
          }}
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex flex-col items-center justify-center text-center py-16 px-8 rounded-xl cursor-pointer transition-all bg-[#0e0e0e] border hover:border-[#f59e0b]/50"
          style={{
            borderStyle: isDragOver ? 'solid' : 'dashed',
            borderColor: isDragOver ? '#f59e0b' : 'rgba(255,255,255,0.12)',
            transform: isDragOver ? 'scale(1.01)' : 'scale(1)',
          }}
        >
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
            style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}
          >
            <span className="material-symbols-outlined text-[36px]" style={{ color: '#f59e0b' }}>
              upload_file
            </span>
          </div>
          <p className="text-[17px] font-bold text-white mb-1">
            Drag & drop drone flight video here
          </p>
          <p className="text-[13px] mb-6 text-[#777]">
            Supported containers: <span className="text-[#aaa] font-mono">MP4 · MOV · AVI · MKV</span> (up to 4.0 GB)
          </p>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold transition-all active:scale-95 cursor-pointer bg-white/5 border border-white/10 text-white hover:bg-white/10"
          >
            <span className="material-symbols-outlined text-[16px]">folder_open</span>
            Browse Files from Computer
          </button>
        </div>
      ) : (
        /* File selected */
        <div className="w-full flex flex-col gap-4">
          <div className="flex flex-col gap-4 p-5 rounded-xl bg-[#0e0e0e] border border-white/10">
            {/* File info row */}
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 overflow-hidden">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}
                >
                  <span className="material-symbols-outlined text-[26px]" style={{ color: '#f59e0b' }}>
                    videocam
                  </span>
                </div>
                <div className="overflow-hidden">
                  <p className="text-[15px] font-bold text-white truncate">{selectedFile.name}</p>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono mt-1 text-[#777]">
                    <span className="text-[#ccc]">{formatFileSize(selectedFile.size)}</span>
                    <span>·</span>
                    <span className="px-1.5 py-0.2 rounded bg-white/5 text-[#f59e0b]">
                      {selectedFile.name.split('.').pop()?.toUpperCase()}
                    </span>
                    {videoDimensions && (
                      <>
                        <span>·</span>
                        <span>{videoDimensions.width}x{videoDimensions.height}</span>
                        <span>·</span>
                        <span>{videoDimensions.duration}s</span>
                      </>
                    )}
                    <span>·</span>
                    <span className="text-emerald-400 font-medium flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      Ready
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="text-[12px] px-3 py-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-40 bg-white/5 border border-white/10 text-[#aaa] hover:text-white"
                >
                  Change
                </button>
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  disabled={isUploading}
                  className="p-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-40 text-red-400 hover:text-red-300"
                  title="Remove video"
                >
                  <span className="material-symbols-outlined text-[20px]">delete</span>
                </button>
              </div>
            </div>

            {/* Video preview if available */}
            {previewUrl && (
              <div className="mt-2 rounded-lg overflow-hidden border border-white/5 bg-black">
                <video
                  src={previewUrl}
                  controls
                  muted
                  playsInline
                  onLoadedMetadata={handleLoadedMetadata}
                  className="w-full max-h-56 object-contain bg-black"
                />
              </div>
            )}
          </div>

          {/* Upload progress */}
          {isUploading && (
            <div className="px-5 py-4 rounded-xl bg-white/[0.02] border border-white/10">
              <div className="flex justify-between items-center text-[12px] font-mono mb-3">
                <span className="flex items-center gap-2 text-[#ccc]">
                  <span className="w-2 h-2 rounded-full bg-[#f59e0b] animate-ping" />
                  Streaming payload to reconstruction server...
                </span>
                <span className="text-[#f59e0b] font-bold">{uploadProgress}%</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden bg-white/10">
                <div
                  className="h-full rounded-full transition-all duration-200"
                  style={{
                    width: `${uploadProgress}%`,
                    background: 'linear-gradient(90deg, #f59e0b, #3b82f6)',
                  }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action CTA */}
      <div className="w-full mt-8 flex justify-end">
        <button
          onClick={handleStart}
          disabled={!selectedFile || isUploading}
          className="flex items-center gap-2 px-8 py-3.5 rounded-lg text-[14px] font-bold transition-all active:scale-[0.97]"
          style={
            selectedFile && !isUploading
              ? {
                  background: 'linear-gradient(135deg,#f59e0b,#d97706)',
                  color: '#000',
                  boxShadow: '0 4px 20px rgba(245,158,11,0.28)',
                  cursor: 'pointer',
                }
              : {
                  background: 'rgba(255,255,255,0.04)',
                  color: '#444',
                  border: '1px solid rgba(255,255,255,0.06)',
                  cursor: 'not-allowed',
                }
          }
        >
          <span className="material-symbols-outlined text-[18px]">
            {isUploading ? 'hourglass_top' : 'rocket_launch'}
          </span>
          {isUploading ? `Uploading Video (${uploadProgress}%)…` : 'Start 3D Reconstruction'}
        </button>
      </div>

      {/* Flight Guidelines */}
      <div className="w-full mt-10 pt-8 border-t border-white/10 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            icon: 'speed',
            title: 'Smooth Flight Trajectory',
            body: 'Continuous orbit or forward pass at 30–50 m AGL. Avoid erratic yaw movements.',
          },
          {
            icon: 'photo_library',
            title: '70%+ Overlap Baseline',
            body: 'Adjacent frames must observe the terrain with ample geometric parallax.',
          },
          {
            icon: 'wb_sunny',
            title: 'Diffused Illumination',
            body: 'Overcast or golden hour flight yields superior photometric correspondence.',
          },
        ].map(({ icon, title, body }) => (
          <div key={title} className="flex flex-col gap-2 p-3 rounded-lg bg-white/[0.01]">
            <div className="flex items-center gap-2 text-[#f59e0b]">
              <span className="material-symbols-outlined text-[18px]">{icon}</span>
              <p className="text-[12px] font-bold text-white">{title}</p>
            </div>
            <p className="text-[12px] leading-[18px] text-[#777]">{body}</p>
          </div>
        ))}
      </div>
    </main>
  );
};
