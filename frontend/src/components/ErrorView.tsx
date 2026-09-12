import React from 'react';
import { ErrorDetails, ErrorType } from '../types';
import { DiagnosticsAccordion } from './DiagnosticsAccordion';

interface ErrorViewProps {
  error: ErrorDetails;
  onRetry?: () => void;
  onUploadDifferent?: () => void;
  onBackToUpload?: () => void;
  onDownloadGlb?: () => void;
}

export const ErrorView: React.FC<ErrorViewProps> = ({
  error,
  onRetry,
  onUploadDifferent,
  onBackToUpload,
  onDownloadGlb,
}) => {
  const getIconForType = (type: ErrorType) => {
    switch (type) {
      case 'unsupported-format':
        return 'warning';
      case 'upload-failed':
        return 'cloud_off';
      case 'poor-footage':
        return 'blur_on';
      case 'no-usable-frames':
        return 'hide_image';
      case 'server-unavailable':
        return 'dns';
      case 'reconstruction-failed':
        return 'error';
      case 'model-loading-failure':
        return 'view_in_ar';
      default:
        return 'error';
    }
  };

  const isWarning = error.type === 'unsupported-format' || error.type === 'poor-footage' || error.type === 'no-usable-frames';

  return (
    <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-6 w-full max-w-xl mx-auto my-auto animate-fade-in">
      <div className="w-full bg-[#101415] border border-[#434655] rounded-xl p-6 md:p-8 flex flex-col items-center text-center shadow-2xl">
        {/* Error / Warning Badge Icon */}
        <div
          className={`w-16 h-16 rounded-full flex items-center justify-center mb-6 ${
            isWarning
              ? 'bg-[#f59e0b]/15 text-[#fbbf24] border border-[#f59e0b]/30'
              : 'bg-[#93000a]/20 text-[#ffb4ab] border border-[#ffb4ab]/30 pulse-error'
          }`}
        >
          <span className="material-symbols-outlined text-[32px]">
            {getIconForType(error.type)}
          </span>
        </div>

        {/* Title */}
        <h1 className="text-[22px] md:text-[24px] font-semibold leading-[30px] text-[#e0e3e5] mb-2 tracking-tight">
          {error.title}
        </h1>

        {/* Description */}
        <p className="text-[14px] leading-[20px] text-[#c3c6d7] max-w-md mb-6">
          {error.message}
        </p>

        {/* Suggested Actions Checklist (for poor footage, etc.) */}
        {error.suggestedActions && error.suggestedActions.length > 0 && (
          <div className="w-full bg-[#0b0f10] border border-[#1E293B] rounded p-4 mb-6 text-left">
            <span className="text-[12px] font-bold tracking-wider uppercase text-[#8d90a0] block mb-2">
              Recommended Footage Guidelines
            </span>
            <ul className="space-y-2 text-[13px] text-[#c3c6d7]">
              {error.suggestedActions.map((action, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="material-symbols-outlined text-[#2563EB] text-[16px] mt-0.5 shrink-0">
                    check_circle
                  </span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 w-full justify-center mb-4">
          {error.type === 'unsupported-format' && (
            <button
              onClick={onUploadDifferent || onBackToUpload}
              className="bg-[#2563EB] text-white px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto shadow-md"
            >
              <span className="material-symbols-outlined text-[18px]">file_upload</span>
              Choose Another Video
            </button>
          )}

          {error.type === 'upload-failed' && (
            <>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="bg-[#2563EB] text-white px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto shadow-md"
                >
                  <span className="material-symbols-outlined text-[18px]">refresh</span>
                  Try Again
                </button>
              )}
              <button
                onClick={onBackToUpload}
                className="bg-[#1d2022] text-[#e0e3e5] border border-[#434655] px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-[#272a2c] active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto"
              >
                <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                Back to Upload
              </button>
            </>
          )}

          {(error.type === 'poor-footage' || error.type === 'no-usable-frames') && (
            <button
              onClick={onUploadDifferent || onBackToUpload}
              className="bg-[#2563EB] text-white px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto shadow-md"
            >
              <span className="material-symbols-outlined text-[18px]">upload_file</span>
              Upload Different Video
            </button>
          )}

          {error.type === 'server-unavailable' && (
            <>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="bg-[#2563EB] text-white px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto shadow-md"
                >
                  <span className="material-symbols-outlined text-[18px]">refresh</span>
                  Try Again
                </button>
              )}
              <button
                onClick={onBackToUpload}
                className="bg-[#1d2022] text-[#e0e3e5] border border-[#434655] px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-[#272a2c] active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto"
              >
                <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                Back to Upload
              </button>
            </>
          )}

          {error.type === 'reconstruction-failed' && (
            <>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="bg-[#2563EB] text-white px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto shadow-md"
                >
                  <span className="material-symbols-outlined text-[18px]">replay</span>
                  Retry Reconstruction
                </button>
              )}
              <button
                onClick={onUploadDifferent || onBackToUpload}
                className="bg-[#1d2022] text-[#e0e3e5] border border-[#434655] px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-[#272a2c] active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto"
              >
                <span className="material-symbols-outlined text-[18px]">upload_file</span>
                Upload Different Video
              </button>
            </>
          )}

          {error.type === 'model-loading-failure' && (
            <>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="bg-[#2563EB] text-white px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto shadow-md"
                >
                  <span className="material-symbols-outlined text-[18px]">refresh</span>
                  Retry View
                </button>
              )}
              {onDownloadGlb && (
                <button
                  onClick={onDownloadGlb}
                  className="bg-[#1d2022] text-[#e0e3e5] border border-[#434655] px-6 py-2.5 rounded text-[13px] font-medium leading-[20px] hover:bg-[#272a2c] active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto"
                >
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  Download GLB
                </button>
              )}
            </>
          )}
        </div>

        {/* Collapsible Diagnostics Accordion */}
        <DiagnosticsAccordion
          code={error.diagnostics?.code || `ERR_${error.type.toUpperCase().replace(/-/g, '_')}`}
          timestamp={error.diagnostics?.timestamp}
          server={error.diagnostics?.server}
          filename={error.diagnostics?.filename}
          mimeType={error.diagnostics?.mimeType}
          details={error.diagnostics?.details || error.message}
          trace={error.diagnostics?.trace}
        />
      </div>
    </main>
  );
};
