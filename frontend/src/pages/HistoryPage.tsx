import React, { useEffect, useState } from 'react';
import { JobHistoryItem } from '../types';
import { listJobs, getDownloadGlbUrl, deleteJob } from '../services/api';

interface HistoryPageProps {
  onSelectJob: (jobId: string, status: string) => void;
  onNavigate: (route: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectJob, onNavigate }) => {
  const [jobs, setJobs] = useState<JobHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchHistory = () => {
    setLoading(true);
    setError(null);
    listJobs(50)
      .then((data) => {
        setJobs(data || []);
        setLoading(false);
      })
      .catch((err) => {
        console.warn('Jobs history fetch error:', err);
        setError(err.message || 'Failed to load jobs from persistent database.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleCopyId = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this reconstruction job and its artifacts from storage?')) {
      try {
        await deleteJob(id);
        setJobs((prev) => prev.filter((j) => (j.job_id || j.id) !== id));
      } catch (err: any) {
        alert(`Failed to delete job: ${err?.message || 'Unknown error'}`);
      }
    }
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Unknown date';
    try {
      const d = new Date(isoString);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <main className="flex-1 flex flex-col p-4 md:p-8 w-full max-w-5xl mx-auto my-auto animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <button
            onClick={() => onNavigate('home')}
            className="flex items-center gap-1.5 text-[12px] font-mono transition-colors cursor-pointer text-[#666] hover:text-white mb-2"
          >
            <span className="material-symbols-outlined text-[15px]">arrow_back</span>
            Back to Home
          </button>
          <h1 className="text-[26px] md:text-[32px] font-black text-white leading-tight">
            Reconstruction Job History
          </h1>
          <p className="text-[13px] text-[#888] mt-1">
            Persistent SQLite audit record of drone video reconstructions on this station.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchHistory}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px] font-medium bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-colors cursor-pointer"
            title="Refresh list"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            Refresh
          </button>
          <button
            onClick={() => onNavigate('upload')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] font-bold text-black transition-all active:scale-95 cursor-pointer"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}
          >
            <span className="material-symbols-outlined text-[16px]">upload</span>
            New Reconstruction
          </button>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="p-12 text-center rounded-xl bg-[#0e0e0e] border border-white/10 text-[#888]">
          <div className="w-8 h-8 border-2 border-[#f59e0b] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-[13px] font-mono">Querying SQLite job database...</p>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="p-6 rounded-xl bg-red-950/30 border border-red-500/40 text-red-200">
          <div className="flex items-center gap-2 font-bold mb-1">
            <span className="material-symbols-outlined text-[18px]">error</span>
            Failed to load jobs
          </div>
          <p className="text-[13px] text-red-300/80 mb-4">{error}</p>
          <button
            onClick={fetchHistory}
            className="px-4 py-1.5 rounded-lg text-[12px] bg-red-900/60 hover:bg-red-800 text-white transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && jobs.length === 0 && (
        <div className="p-16 text-center rounded-xl bg-[#0e0e0e] border border-white/10">
          <span className="material-symbols-outlined text-[48px] text-[#444] mb-3">
            folder_open
          </span>
          <h3 className="text-[16px] font-bold text-white mb-1">No Reconstruction Jobs Found</h3>
          <p className="text-[13px] text-[#777] max-w-sm mx-auto mb-6">
            Upload your first drone flight video to initialize photogrammetric processing.
          </p>
          <button
            onClick={() => onNavigate('upload')}
            className="px-6 py-2.5 rounded-lg text-[13px] font-bold text-black"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}
          >
            Upload Flight Video
          </button>
        </div>
      )}

      {/* Jobs List */}
      {!loading && !error && jobs.length > 0 && (
        <div className="flex flex-col gap-3">
          {jobs.map((job) => {
            const jid = job.job_id || job.id;
            const isComplete = ['complete', 'completed'].includes(job.status);
            const isProcessing = ['processing', 'queued'].includes(job.status);
            const isFailed = job.status === 'failed';

            return (
              <div
                key={jid}
                onClick={() => onSelectJob(jid, job.status)}
                className="p-4 md:p-5 rounded-xl bg-[#0e0e0e] border border-white/10 hover:border-white/20 transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
              >
                {/* Left job info */}
                <div className="flex items-start gap-4 overflow-hidden">
                  <div
                    className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                      isComplete
                        ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                        : isFailed
                        ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                        : 'bg-blue-500/10 border border-blue-500/30 text-blue-400'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[24px]">
                      {isComplete ? 'view_in_ar' : isFailed ? 'error' : 'hourglass_top'}
                    </span>
                  </div>

                  <div className="overflow-hidden">
                    <div className="flex items-center gap-2">
                      <p className="text-[15px] font-bold text-white truncate group-hover:text-[#f59e0b] transition-colors">
                        {job.filename}
                      </p>
                      <span
                        className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold ${
                          isComplete
                            ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/30'
                            : isFailed
                            ? 'bg-red-950/40 text-red-400 border border-red-500/30'
                            : 'bg-blue-950/40 text-blue-400 border border-blue-500/30 animate-pulse'
                        }`}
                      >
                        {job.status}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono mt-1 text-[#777]">
                      <span className="text-[#aaa]">{formatDate(job.created_at)}</span>
                      <span>·</span>
                      <span className="flex items-center gap-1 text-[#888]">
                        ID: {jid.substring(0, 8)}...
                        <button
                          onClick={(e) => handleCopyId(jid, e)}
                          className="hover:text-white p-0.5"
                          title="Copy full UUID"
                        >
                          <span className="material-symbols-outlined text-[13px]">
                            {copiedId === jid ? 'check' : 'content_copy'}
                          </span>
                        </button>
                      </span>
                      {job.stage_message && (
                        <>
                          <span>·</span>
                          <span className="text-[#aaa] truncate max-w-[200px]">{job.stage_message}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Actions */}
                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  {isComplete && (
                    <>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectJob(jid, 'complete');
                        }}
                        className="bg-[#2563EB] hover:bg-blue-500 text-white px-3.5 py-1.5 rounded-lg text-[12px] font-bold transition-all active:scale-95 flex items-center gap-1.5 cursor-pointer shadow-sm"
                      >
                        <span className="material-symbols-outlined text-[16px]">view_in_ar</span>
                        View 3D
                      </button>

                      <a
                        href={getDownloadGlbUrl(jid)}
                        onClick={(e) => e.stopPropagation()}
                        download
                        className="bg-white/5 hover:bg-white/10 text-white border border-white/10 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-colors flex items-center gap-1.5 cursor-pointer"
                        title="Download GLB"
                      >
                        <span className="material-symbols-outlined text-[16px]">download</span>
                        GLB
                      </a>
                    </>
                  )}

                  {isProcessing && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectJob(jid, 'processing');
                      }}
                      className="bg-blue-600/30 hover:bg-blue-600/50 text-blue-200 border border-blue-500/40 px-3.5 py-1.5 rounded-lg text-[12px] font-medium transition-colors flex items-center gap-1.5 cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[16px] animate-spin">refresh</span>
                      Track ({job.progress_percent || 0}%)
                    </button>
                  )}

                  <button
                    onClick={(e) => handleDelete(jid, e)}
                    className="p-1.5 rounded-lg text-[#666] hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                    title="Delete job"
                  >
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
};
