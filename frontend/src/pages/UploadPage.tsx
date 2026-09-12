import React, { useRef, useState } from 'react';

interface UploadPageProps {
  onStartReconstruction: (file: File) => void;
  onUnsupportedFormat: (file: File) => void;
  onNavigate: (route: string) => void;
  isUploading?: boolean;
  uploadProgress?: number;
}

export const UploadPage: React.FC<UploadPageProps> = ({
  onStartReconstruction,
  onUnsupportedFormat,
  onNavigate,
  isUploading = false,
  uploadProgress = 0,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['mp4', 'mov', 'avi'];

  const validateAndSetFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !allowedExtensions.includes(ext)) {
      onUnsupportedFormat(file);
      return;
    }
    setSelectedFile(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) validateAndSetFile(e.target.files[0]);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) validateAndSetFile(e.dataTransfer.files[0]);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const handleStart = () => {
    if (selectedFile && !isUploading) onStartReconstruction(selectedFile);
  };

  return (
    <main
      className="flex-1 flex flex-col items-center justify-center p-5 md:p-10 w-full max-w-2xl mx-auto my-auto"
      style={{ minHeight: 'calc(100vh - 56px)' }}
    >
      {/* Back link */}
      <div className="w-full mb-6">
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-1.5 text-[12px] font-mono transition-colors cursor-pointer"
          style={{ color: '#555' }}
          onMouseEnter={e => (e.currentTarget.style.color = '#f0f0f0')}
          onMouseLeave={e => (e.currentTarget.style.color = '#555')}
        >
          <span className="material-symbols-outlined text-[15px]">arrow_back</span>
          Back
        </button>
      </div>

      {/* Title */}
      <div className="w-full mb-8">
        <h1 className="text-[28px] md:text-[34px] font-black text-white leading-tight mb-2">
          Upload your footage
        </h1>
        <p className="text-[14px] leading-[22px]" style={{ color: '#666' }}>
          We handle everything — frame filtering, feature matching, meshing. Just drop the video.
        </p>
      </div>

      {/* Hidden input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".mp4,.mov,.avi,video/mp4,video/quicktime,video/x-msvideo"
        onChange={handleFileChange}
        className="hidden"
        id="drone-video-file-input"
      />

      {/* Drop zone */}
      {!selectedFile ? (
        <div
          onDrop={handleDrop}
          onDragOver={e => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={e => { e.preventDefault(); setIsDragOver(false); }}
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex flex-col items-center justify-center text-center py-16 px-8 rounded-xl cursor-pointer transition-all"
          style={{
            border: isDragOver ? '1.5px solid #f59e0b' : '1.5px dashed rgba(255,255,255,0.1)',
            background: isDragOver ? 'rgba(245,158,11,0.04)' : 'rgba(255,255,255,0.02)',
            transform: isDragOver ? 'scale(1.01)' : 'scale(1)',
          }}
        >
          <span className="material-symbols-outlined text-[48px] mb-5" style={{ color: isDragOver ? '#f59e0b' : '#333' }}>
            video_file
          </span>
          <p className="text-[16px] font-semibold text-white mb-1">
            Drag your video here
          </p>
          <p className="text-[13px] mb-7" style={{ color: '#555' }}>
            MP4 · MOV · AVI
          </p>
          <button
            type="button"
            onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold transition-all active:scale-95 cursor-pointer"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#aaa',
            }}
          >
            <span className="material-symbols-outlined text-[16px]">folder_open</span>
            Browse files
          </button>
        </div>
      ) : (
        /* File selected */
        <div className="w-full flex flex-col gap-4">
          <div
            className="flex items-center justify-between gap-4 px-5 py-4 rounded-xl"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            <div className="flex items-center gap-4 overflow-hidden">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}
              >
                <span className="material-symbols-outlined text-[22px]" style={{ color: '#f59e0b' }}>video_file</span>
              </div>
              <div className="overflow-hidden">
                <p className="text-[14px] font-semibold text-white truncate">{selectedFile.name}</p>
                <div className="flex items-center gap-2 text-[11px] font-mono mt-0.5" style={{ color: '#555' }}>
                  <span>{formatFileSize(selectedFile.size)}</span>
                  <span>·</span>
                  <span>{selectedFile.name.split('.').pop()?.toUpperCase()}</span>
                  <span>·</span>
                  <span style={{ color: '#22c55e' }}>ready</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="text-[12px] px-3 py-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-40"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: '#888' }}
              >
                Change
              </button>
              <button
                type="button"
                onClick={handleRemoveFile}
                disabled={isUploading}
                className="p-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-40"
                style={{ color: '#ef4444' }}
              >
                <span className="material-symbols-outlined text-[19px]">delete</span>
              </button>
            </div>
          </div>

          {/* Upload progress */}
          {isUploading && (
            <div
              className="px-5 py-4 rounded-xl"
              style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}
            >
              <div className="flex justify-between items-center text-[12px] font-mono mb-3">
                <span className="flex items-center gap-2" style={{ color: '#aaa' }}>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b] animate-pulse" />
                  Uploading to reconstruction server
                </span>
                <span style={{ color: '#f59e0b' }}>{uploadProgress}%</span>
              </div>
              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                <div
                  className="h-full rounded-full shimmer transition-all duration-200"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Checklist */}
          <div className="flex flex-wrap gap-x-5 gap-y-1.5 px-1">
            {[
              'SfM + Bundle Adjustment',
              'Outputs GLB + OBJ',
              'Runs on server',
            ].map(t => (
              <span key={t} className="flex items-center gap-1.5 text-[12px]" style={{ color: '#555' }}>
                <span className="w-1 h-1 rounded-full bg-[#f59e0b] opacity-60" />
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action */}
      <div className="w-full mt-8 flex justify-end">
        <button
          onClick={handleStart}
          disabled={!selectedFile || isUploading}
          className="flex items-center gap-2 px-7 py-3 rounded-lg text-[14px] font-bold transition-all active:scale-[0.97]"
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
                color: '#333',
                border: '1px solid rgba(255,255,255,0.06)',
                cursor: 'not-allowed',
              }
          }
        >
          <span className="material-symbols-outlined text-[18px]">
            {isUploading ? 'hourglass_top' : 'play_arrow'}
          </span>
          {isUploading ? 'Uploading…' : 'Start reconstruction'}
        </button>
      </div>

      {/* Tips */}
      <div className="w-full mt-10 pt-8 border-t grid grid-cols-1 md:grid-cols-3 gap-6" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
        {[
          { title: 'Fly slow and steady', body: 'Constant altitude, 30–50 m AGL. Smooth forward flight beats erratic coverage.' },
          { title: '70%+ frame overlap', body: 'The more overlap between consecutive frames, the better the feature matcher performs.' },
          { title: 'Avoid harsh shadows', body: 'Overcast or golden hour beats noon sun. Moving shadows confuse depth estimation.' },
        ].map(({ title, body }) => (
          <div key={title}>
            <p className="text-[12px] font-semibold text-white mb-1">{title}</p>
            <p className="text-[12px] leading-[19px]" style={{ color: '#555' }}>{body}</p>
          </div>
        ))}
      </div>
    </main>
  );
};
