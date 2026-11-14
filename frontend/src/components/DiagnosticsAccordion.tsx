import React, { useState } from 'react';

interface DiagnosticsAccordionProps {
  code?: string;
  timestamp?: string;
  server?: string;
  filename?: string;
  mimeType?: string;
  details?: string;
  trace?: string;
  title?: string;
  defaultExpanded?: boolean;
}

export const DiagnosticsAccordion: React.FC<DiagnosticsAccordionProps> = ({
  code = 'ERR_PROCESSING_HALTED',
  timestamp = new Date().toISOString(),
  server = 'geoforge-reconstruction-node-01',
  filename,
  mimeType,
  details,
  trace,
  title = 'Technical Diagnostics',
  defaultExpanded = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="w-full border border-[#434655] rounded bg-[#101415] overflow-hidden text-left mt-4">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex justify-between items-center bg-[#1d2022] hover:bg-[#272a2c] transition-colors focus:outline-none cursor-pointer"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-2 text-[#c3c6d7]">
          <span className="material-symbols-outlined text-[18px]">terminal</span>
          <span className="text-[12px] font-medium tracking-[0.02em] text-[#e0e3e5]">
            {title}
          </span>
        </div>
        <span
          className={`material-symbols-outlined text-[#8d90a0] text-[20px] transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
        >
          expand_more
        </span>
      </button>

      {isExpanded && (
        <div className="border-t border-[#434655] p-4 bg-[#0b0f10] font-mono text-[12px] leading-[18px] text-[#c3c6d7]">
          <div className="flex flex-col gap-2">
            <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
              <span className="text-[#8d90a0]">TIMESTAMP:</span>
              <span className="text-[#e0e3e5]">{timestamp}</span>
            </div>
            <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
              <span className="text-[#8d90a0]">ERROR_CODE:</span>
              <span className="text-[#ffb4ab] font-bold">{code}</span>
            </div>
            <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
              <span className="text-[#8d90a0]">NODE_SERVICE:</span>
              <span className="text-[#bec6e0]">{server}</span>
            </div>
            {filename && (
              <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
                <span className="text-[#8d90a0]">INPUT_FILE:</span>
                <span className="text-[#e0e3e5]">{filename}</span>
              </div>
            )}
            {mimeType && (
              <div className="flex justify-between border-b border-[#1E293B] pb-1.5">
                <span className="text-[#8d90a0]">MIME_TYPE:</span>
                <span className="text-[#e0e3e5]">{mimeType}</span>
              </div>
            )}
            {details && (
              <div className="pt-1">
                <span className="text-[#8d90a0] block mb-1">DIAGNOSTIC_MSG:</span>
                <div className="bg-[#020617] p-2.5 rounded border border-[#1E293B] text-[#ffb4ab] whitespace-pre-wrap">
                  {details}
                </div>
              </div>
            )}
            {trace && (
              <div className="pt-1">
                <span className="text-[#8d90a0] block mb-1">TRACE_LOG:</span>
                <div className="bg-[#020617] p-2.5 rounded border border-[#1E293B] text-[#bec6e0] whitespace-pre-wrap max-h-36 overflow-y-auto">
                  {trace}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
