import React, { useRef, useState } from 'react';

import { Header } from './components/Header';
import { Footer } from './components/Footer';

import { HomePage } from './pages/HomePage';
import { HowItWorksPage } from './pages/HowItWorksPage';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage, PIPELINE_STAGES } from './pages/ProcessingPage';
import { CompletePage } from './pages/CompletePage';
import { ResultPage } from './pages/ResultPage';
import { HistoryPage } from './pages/HistoryPage';

import { ErrorView } from './components/ErrorView';

import {
  ErrorDetails,
  ReconstructionJob,
  UploadResponse,
} from './types';

import {
  API_BASE_URL,
  uploadDroneVideo,
  getJobStatus,
  getModelGlbUrl,
  cancelJob,
} from './services/api';


type AppRoute =
  | 'home'
  | 'how-it-works'
  | 'upload'
  | 'processing'
  | 'complete'
  | 'result'
  | 'history'
  | 'error';


export default function App() {

  // ============================================================
  // ROUTING
  // ============================================================

  const [currentRoute, setCurrentRoute] =
    useState<AppRoute>('home');


  // ============================================================
  // UPLOAD STATE
  // ============================================================

  const [isUploading, setIsUploading] =
    useState(false);

  const [uploadProgress, setUploadProgress] =
    useState(0);


  // ============================================================
  // JOB STATE
  // ============================================================

  const [currentJob, setCurrentJob] =
    useState<ReconstructionJob | null>(null);


  // ============================================================
  // ERROR STATE
  // ============================================================

  const [currentError, setCurrentError] =
    useState<ErrorDetails | null>(null);


  // ============================================================
  // LAST UPLOADED FILE
  // ============================================================

  const [lastUploadedFile, setLastUploadedFile] =
    useState<File | null>(null);


  // ============================================================
  // ACTIVE POLL INTERVAL REF
  // Stored in a ref so it can be cleared from anywhere (catch,
  // cancel, etc.) without causing re-renders.
  // ============================================================

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ============================================================
  // STAGE MAPPING HELPER
  // ============================================================
  const mapBackendStageToIndex = (stage: string): number => {
    switch (stage) {
      case 'video_uploaded':
      case 'uploading':
      case 'queued':
      case 'validating_video':
        return 0;
      case 'extracting_frames':
        return 1;
      case 'filtering_frames':
      case 'filtering_images':
      case 'filtering_blurry':
      case 'redundancy_filter':
      case 'removing_redundant':
        return 2;
      case 'extracting_features':
      case 'feature_extraction':
        return 3;
      case 'matching_features':
      case 'feature_matching':
        return 4;
      case 'sparse_reconstruction':
      case 'sparse_quality_check':
      case 'camera_reconstruction':
        return 5;
      case 'image_undistortion':
      case 'dense_stereo':
      case 'stereo_fusion':
      case 'dense_reconstruction':
        return 6;
      case 'processing_pointcloud':
      case 'point_cloud_cleaning':
        return 7;
      case 'generating_mesh':
      case 'poisson_meshing':
        return 8;
      case 'generating_texture':
      case 'texture_mapping':
        return 9;
      case 'exporting_glb':
        return 10;
      case 'validating_model':
      case 'completed':
      case 'complete':
        return 11;
      default:
        return 0;
    }
  };

  // ============================================================
  // RESTORE JOB ON MOUNT (F5 REFRESH / URL QUERY PERSISTENCE)
  // ============================================================
  React.useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const urlJobId = params.get('job_id');
      const savedJobId = urlJobId || localStorage.getItem('geoforge_last_job_id');

      if (savedJobId && savedJobId.length > 10) {
        getJobStatus(savedJobId)
          .then((statusData) => {
            const status = (statusData?.status || '').toLowerCase();
            if (status === 'complete' || status === 'completed') {
              const modelUrl = getModelGlbUrl(savedJobId);
              const restoredJob: ReconstructionJob = {
                jobId: savedJobId,
                filename: statusData.filename || 'reconstructed_model.mp4',
                fileSize: 0,
                fileSizeBytesFormatted: 'Restored Model',
                currentStageIndex: 9,
                currentStageName: 'Preparing 3D model',
                overallStatus: 'completed',
                backendMessage: statusData.message || 'Model successfully restored from persistent storage.',
                glbUrl: modelUrl,
                meshObjReady: true,
                pointCloudLasReady: false,
                orthomosaicTiffReady: false,
              };
              setCurrentJob(restoredJob);
              setCurrentRoute('result');
            }
          })
          .catch((err) => {
            console.warn('Could not restore previous job on mount:', err);
          });
      }
    } catch (e) {
      console.warn('Storage access warning:', e);
    }
  }, []);


  // ============================================================
  // FORMAT FILE SIZE
  // ============================================================

  const formatBytes = (bytes: number): string => {

    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    if (bytes < 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };


  // ============================================================
  // ERROR HANDLER
  // ============================================================

  const triggerError = (error: ErrorDetails) => {

    setCurrentError(error);

    setCurrentRoute('error');
  };


  // ============================================================
  // CONVERT BACKEND MODEL URL
  // ============================================================

  const resolveModelUrl = (
    modelUrl?: string
  ): string | undefined => {

    if (!modelUrl) {
      return undefined;
    }

    return getModelGlbUrl(modelUrl);
  };


  // ============================================================
  // START RECONSTRUCTION
  // ============================================================

  const handleStartReconstruction = async (
    file: File
  ) => {

    setLastUploadedFile(file);

    setIsUploading(true);

    setUploadProgress(0);


    // ------------------------------------------------------------
    // TEMPORARY LOCAL JOB ID
    // ------------------------------------------------------------

    const temporaryJobId =
      `GF-${Date.now().toString(36).toUpperCase()}`;


    // ------------------------------------------------------------
    // CREATE INITIAL JOB
    // ------------------------------------------------------------

    const newJob: ReconstructionJob = {

      jobId: temporaryJobId,

      filename: file.name,

      fileSize: file.size,

      fileSizeBytesFormatted:
        formatBytes(file.size),

      currentStageIndex: 0,

      currentStageName:
        PIPELINE_STAGES[0]?.label ||
        'Video uploaded',

      overallStatus: 'processing',

      backendMessage:
        'Uploading video to FastAPI reconstruction engine...',

      glbUrl: undefined,

      meshObjReady: false,

      pointCloudLasReady: false,

      orthomosaicTiffReady: false,

      coordinateSystem: undefined,

      processingQuality: undefined,

    };


    setCurrentJob(newJob);


    // ------------------------------------------------------------
    // SHOW PROCESSING PAGE IMMEDIATELY
    // ------------------------------------------------------------

    setCurrentRoute('processing');


    try {

      // ==========================================================
      // SEND VIDEO TO BACKEND
      // ==========================================================

      const response: UploadResponse =
        await uploadDroneVideo(
          file,
          (progress) => {

            setUploadProgress(
              progress.percentage
            );

            setCurrentJob((previous) => {

              if (!previous) {
                return previous;
              }

              return {

                ...previous,

                backendMessage:
                  progress.percentage < 100
                    ? `Uploading video... ${progress.percentage}%`
                    : 'Video uploaded. Running reconstruction pipeline...',

              };

            });

          }
        );


      // ==========================================================
      // UPLOAD REQUEST FINISHED — backend accepted the job
      // ==========================================================

      setIsUploading(false);


      // ==========================================================
      // GET REAL BACKEND JOB ID
      // ==========================================================

      const confirmedJobId =
        response.job_id ||
        response.id ||
        temporaryJobId;

      try {
        localStorage.setItem('geoforge_last_job_id', confirmedJobId);
        window.history.replaceState(null, '', `?job_id=${encodeURIComponent(confirmedJobId)}`);
      } catch (e) {
        console.warn('Storage warning:', e);
      }


      // ==========================================================
      // START POLLING /status/{job_id} with exponential back-off
      // ==========================================================
      //
      // Poll cadence: 3 s → 5 s → 10 s → 20 s → 30 s (cap)
      //
      // ==========================================================

      const POLL_DELAYS_MS = [3000, 5000, 10000, 20000, 30000];
      const TOTAL_STAGES = 12;
      const MAX_PROCESSING_INDEX = TOTAL_STAGES - 2;
      let pollStep = 0;

      const schedulePoll = () => {
        const delay = POLL_DELAYS_MS[Math.min(pollStep, POLL_DELAYS_MS.length - 1)];
        pollStep += 1;

        pollIntervalRef.current = setTimeout(async () => {

          try {

            const statusData = await getJobStatus(confirmedJobId);
            const backendStatus: string = (statusData?.status ?? '').toLowerCase();


            // --------------------------------------------------------
            // COMPLETE
            // --------------------------------------------------------

            if (
              backendStatus === 'complete' ||
              backendStatus === 'completed' ||
              backendStatus === 'success'
            ) {
              const result = statusData?.result ?? {};
              const backendModelUrl =
                result.model_url ||
                response.model_url ||
                response.glb_url;

              const resolvedModelUrl = resolveModelUrl(backendModelUrl);

              setCurrentJob((previous) => {
                if (!previous) return previous;
                return {
                  ...previous,
                  jobId: confirmedJobId,
                  glbUrl: resolvedModelUrl,
                  overallStatus: 'completed',
                  currentStageIndex: TOTAL_STAGES - 1,
                  currentStageName: 'Validating model',
                  progressPercent: 100,
                  backendMessage:
                    result.pipeline_status === 'complete'
                      ? 'Reconstruction completed successfully.'
                      : statusData?.message || 'Reconstruction completed.',
                };
              });

              setCurrentRoute('complete');
              return; // stop polling
            }


            // --------------------------------------------------------
            // FAILED
            // --------------------------------------------------------

            if (backendStatus === 'failed') {
              const errMsg =
                statusData?.error || 'Reconstruction failed on the server.';

              setCurrentJob((previous) => {
                if (!previous) return previous;
                return { ...previous, jobId: confirmedJobId, overallStatus: 'failed', backendMessage: errMsg };
              });

              triggerError({
                type: 'reconstruction-failed',
                title: '3D Reconstruction Failed',
                message: errMsg,
                diagnostics: {
                  code: 'ERR_RECONSTRUCTION_PIPELINE',
                  timestamp: new Date().toISOString(),
                  server: API_BASE_URL,
                  filename: file.name,
                  details: errMsg,
                },
              });

              return; // stop polling
            }


            // --------------------------------------------------------
            // STILL PROCESSING / QUEUED — update stage from backend
            // --------------------------------------------------------

            const backendStage = statusData?.stage || '';
            const mappedIndex = mapBackendStageToIndex(backendStage);

            setCurrentJob((previous) => {
              if (!previous) return previous;
              const nextIndex = Math.max(previous.currentStageIndex, mappedIndex);
              return {
                ...previous,
                jobId: confirmedJobId,
                currentStageIndex: nextIndex,
                currentStageName: PIPELINE_STAGES[nextIndex]?.label || `Processing stage ${nextIndex + 1}`,
                progressPercent: statusData?.progress_percent,
                backendMessage:
                  statusData?.stage_message ||
                  statusData?.message ||
                  (backendStatus === 'queued'
                    ? 'Job is queued on the reconstruction server...'
                    : `Running reconstruction pipeline... (stage ${nextIndex + 1} of ${TOTAL_STAGES})`),
              };
            });

            schedulePoll(); // schedule next poll with increased delay

          } catch (pollErr: any) {

            // --------------------------------------------------------
            // 404 = job not found (server restarted / job expired)
            // Stop polling immediately and show a clear error.
            // --------------------------------------------------------
            if (pollErr?.status === 404) {
              triggerError({
                type: 'server-unavailable',
                title: 'Job No Longer Found',
                message:
                  'The reconstruction job could not be found on the server. ' +
                  'The backend may have been restarted. Please upload your video again.',
                diagnostics: {
                  code: 'ERR_JOB_NOT_FOUND_404',
                  timestamp: new Date().toISOString(),
                  server: API_BASE_URL,
                  filename: file.name,
                  details: pollErr?.message,
                },
              });
              return; // stop polling
            }

            // Other errors (network blip, 500) — retry with back-off
            console.warn('Status poll failed (will retry):', pollErr?.message);
            schedulePoll();
          }

        }, delay);
      };

      schedulePoll();

    } catch (err: any) {

      // ==========================================================
      // RESET UPLOAD STATE + STOP ANY PENDING POLL
      // ==========================================================

      if (pollIntervalRef.current !== null) {
        clearTimeout(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }

      setIsUploading(false);


      const message =
        err?.message ||
        'Unknown reconstruction error';


      const status =
        err?.status;


      // ==========================================================
      // NETWORK ERROR
      // ==========================================================

      const isNetworkError =
        err?.isNetworkError ||
        message.includes('NetworkError') ||
        message.includes('Failed to fetch') ||
        message.includes('ERR_CONNECTION_REFUSED') ||
        !status;


      if (isNetworkError) {

        triggerError({

          type: 'server-unavailable',

          title:
            'Reconstruction Server Unavailable',

          message:
            `Cannot connect to the GeoForge backend service at ${API_BASE_URL}. ` +
            `Make sure FastAPI is running.`,

          diagnostics: {

            code:
              'ERR_BACKEND_CONNECTION_REFUSED',

            timestamp:
              new Date().toISOString(),

            server:
              API_BASE_URL,

            filename:
              file.name,

            mimeType:
              file.type || 'video/*',

            details:
              message,

            trace:
              `POST ${API_BASE_URL}/upload failed.\n` +
              `Make sure the backend is running with:\n` +
              `uvicorn main:app --reload`,

          },

        });

        return;
      }


      // ==========================================================
      // INVALID FORMAT
      // ==========================================================

      if (
        status === 400 ||
        status === 415
      ) {

        triggerError({

          type: 'unsupported-format',

          title:
            'Unsupported Video Format',

          message:
            'The uploaded video format is not supported. ' +
            'GeoForge accepts MP4, MOV, AVI and MKV files.',

          diagnostics: {

            code:
              'ERR_INVALID_VIDEO_FORMAT',

            timestamp:
              new Date().toISOString(),

            server:
              API_BASE_URL,

            filename:
              file.name,

            mimeType:
              file.type || 'unknown',

            details:
              message,

          },

        });

        return;
      }


      // ==========================================================
      // VALIDATION / FOOTAGE ERROR
      // ==========================================================

      if (status === 422) {

        triggerError({

          type: 'poor-footage',

          title:
            'Reconstruction Could Not Be Completed',

          message:
            'The backend could not successfully reconstruct a 3D model from this footage.',

          suggestedActions: [

            'Use higher-resolution drone footage.',

            'Keep the drone movement slow and stable.',

            'Maintain strong overlap between consecutive views.',

            'Avoid excessive motion blur.',

            'Use footage containing detailed visual features.',

          ],

          diagnostics: {

            code:
              'ERR_RECONSTRUCTION_VALIDATION',

            timestamp:
              new Date().toISOString(),

            server:
              API_BASE_URL,

            filename:
              file.name,

            details:
              message,

          },

        });

        return;
      }


      // ==========================================================
      // GENERAL RECONSTRUCTION ERROR
      // ==========================================================

      triggerError({

        type:
          'reconstruction-failed',

        title:
          '3D Reconstruction Failed',

        message:
          message,

        diagnostics: {

          code:
            `ERR_HTTP_${status || 'UNKNOWN'}`,

          timestamp:
            new Date().toISOString(),

          server:
            API_BASE_URL,

          filename:
            file.name,

          details:
            message,

          trace:
            JSON.stringify(
              err?.response || {},
              null,
              2
            ),

        },

      });

    }

  };


  // ============================================================
  // UNSUPPORTED FILE HANDLER
  // ============================================================

  const handleUnsupportedFormat = (
    file: File
  ) => {

    triggerError({

      type:
        'unsupported-format',

      title:
        'Unsupported Video Format',

      message:
        `The file "${file.name}" is not supported. ` +
        `GeoForge accepts MP4, MOV, AVI and MKV video files.`,

      diagnostics: {

        code:
          'ERR_UNSUPPORTED_MIME_TYPE',

        timestamp:
          new Date().toISOString(),

        filename:
          file.name,

        mimeType:
          file.type || 'unknown',

        details:
          `Detected extension: .${file.name.split('.').pop() || 'unknown'}`,

      },

    });

  };


  // ============================================================
  // RETRY
  // ============================================================

  const handleRetryUpload = () => {

    if (lastUploadedFile) {

      handleStartReconstruction(
        lastUploadedFile
      );

      return;
    }

    setCurrentRoute('upload');

  };


  // ============================================================
  // DOWNLOAD GLB
  // ============================================================

  const handleDownloadGlb = () => {

    if (!currentJob) {
      return;
    }


    if (!currentJob.glbUrl) {

      console.error(
        'No GLB model URL available.'
      );

      return;
    }


    const link =
      document.createElement('a');


    link.href =
      currentJob.glbUrl;


    link.download =
      `${currentJob.filename.replace(/\.[^/.]+$/, '')}_reconstruction.glb`;


    link.target =
      '_blank';


    link.rel =
      'noopener noreferrer';


    document.body.appendChild(
      link
    );


    link.click();


    document.body.removeChild(
      link
    );

  };


  // ============================================================
  // MODEL LOADING ERROR
  // ============================================================

  const handleModelLoadError = (
    error: Error
  ) => {

    console.error(
      'Three.js model loading failed:',
      error
    );


    if (!currentJob) {
      return;
    }


    setCurrentJob((previous) => {

      if (!previous) {
        return previous;
      }

      return {

        ...previous,

        backendMessage:
          '3D model could not be loaded by the browser.',

        error: {

          type:
            'model-loading-failure',

          title:
            '3D Model Loading Failed',

          message:
            error.message ||
            'The GLB model could not be loaded.',

          diagnostics: {

            code:
              'ERR_GLTF_MODEL_LOAD',

            timestamp:
              new Date().toISOString(),

            server:
              API_BASE_URL,

            filename:
              previous.filename,

            details:
              error.message,

          },

        },

      };

    });

  };


  // ============================================================
  // NAVIGATION HELPER
  // ============================================================

  const navigate = (
    route: string
  ) => {

    setCurrentRoute(
      route as AppRoute
    );

  };


  // ============================================================
  // HISTORY JOB SELECTION
  // ============================================================

  const handleSelectHistoryJob = async (selectedJobId: string, status: string) => {
    try {
      const statusData = await getJobStatus(selectedJobId);
      const resolvedModelUrl = getModelGlbUrl(selectedJobId);
      const st = (statusData?.status || status || '').toLowerCase();
      const isComplete = st === 'complete' || st === 'completed';

      const loadedJob: ReconstructionJob = {
        jobId: selectedJobId,
        filename: statusData?.filename || 'flight_video.mp4',
        fileSize: 0,
        fileSizeBytesFormatted: 'Stored Job',
        currentStageIndex: isComplete ? 11 : mapBackendStageToIndex(statusData?.stage || ''),
        currentStageName: isComplete ? 'Model validation' : (statusData?.stage_message || 'Processing'),
        overallStatus: isComplete ? 'completed' : (st === 'failed' ? 'failed' : 'processing'),
        backendMessage: statusData?.stage_message || statusData?.message || (isComplete ? 'Reconstruction complete!' : 'Active reconstruction'),
        glbUrl: isComplete ? resolvedModelUrl : undefined,
        progressPercent: statusData?.progress_percent ?? (isComplete ? 100 : 0),
      };

      setCurrentJob(loadedJob);
      try {
        localStorage.setItem('geoforge_last_job_id', selectedJobId);
        window.history.replaceState(null, '', `?job_id=${encodeURIComponent(selectedJobId)}`);
      } catch (e) {
        console.warn('Storage warning:', e);
      }

      if (isComplete) {
        setCurrentRoute('result');
      } else {
        setCurrentRoute('processing');
      }
    } catch (err) {
      console.error('Error loading history job:', err);
    }
  };


  // ============================================================
  // RENDER
  // ============================================================

  return (

    <div
      className="
        min-h-screen
        flex
        flex-col
        bg-[#020617]
        text-[#e0e3e5]
        font-sans
        antialiased
      "
    >

      {/* ======================================================
          HEADER
      ====================================================== */}

      <Header
        currentRoute={
          currentRoute
        }
        onNavigate={
          navigate
        }
      />


      {/* ======================================================
          HOME
      ====================================================== */}

      {currentRoute === 'home' && (

        <HomePage
          onNavigate={
            navigate
          }
        />

      )}


      {/* ======================================================
          HOW IT WORKS
      ====================================================== */}

      {currentRoute === 'how-it-works' && (

        <HowItWorksPage
          onNavigate={
            navigate
          }
        />

      )}


      {/* ======================================================
          JOB HISTORY
      ====================================================== */}

      {currentRoute === 'history' && (

        <HistoryPage
          onSelectJob={
            handleSelectHistoryJob
          }
          onNavigate={
            navigate
          }
        />

      )}


      {/* ======================================================
          UPLOAD
      ====================================================== */}

      {currentRoute === 'upload' && (

        <UploadPage

          onStartReconstruction={
            handleStartReconstruction
          }

          onUnsupportedFormat={
            handleUnsupportedFormat
          }

          onNavigate={
            navigate
          }

          isUploading={
            isUploading
          }

          uploadProgress={
            uploadProgress
          }

        />

      )}


      {/* ======================================================
          PROCESSING
      ====================================================== */}

      {currentRoute === 'processing' &&
        currentJob && (

          <ProcessingPage

            job={
              currentJob
            }

            onCancel={() => {

              if (
                window.confirm(
                  'Are you sure you want to cancel the current reconstruction?'
                )
              ) {

                setCurrentRoute(
                  'upload'
                );

              }

            }}

            onRetry={() => {

              if (
                lastUploadedFile
              ) {

                handleStartReconstruction(
                  lastUploadedFile
                );

              }

            }}

            onUploadDifferent={() => {

              setCurrentJob(
                null
              );

              setCurrentRoute(
                'upload'
              );

            }}

            onViewResult={() => {

              setCurrentRoute(
                'result'
              );

            }}

          />

        )}


      {/* ======================================================
          COMPLETE
      ====================================================== */}

      {currentRoute === 'complete' &&
        currentJob && (

          <CompletePage

            job={
              currentJob
            }

            onView3DModel={() => {

              setCurrentRoute(
                'result'
              );

            }}

            onDownloadGlb={
              handleDownloadGlb
            }

            onUploadAnother={() => {

              setCurrentJob(
                null
              );

              setCurrentError(
                null
              );

              setUploadProgress(
                0
              );

              setCurrentRoute(
                'upload'
              );

            }}

            onNavigate={
              navigate
            }

          />

        )}


      {/* ======================================================
          3D RESULT
      ====================================================== */}

      {currentRoute === 'result' &&
        currentJob && (

          <ResultPage

            job={
              currentJob
            }

            onNewReconstruction={() => {

              setCurrentJob(
                null
              );

              setCurrentError(
                null
              );

              setUploadProgress(
                0
              );

              setCurrentRoute(
                'upload'
              );

            }}

            onDownloadGlb={
              handleDownloadGlb
            }

            onModelLoadError={
              handleModelLoadError
            }

            onNavigate={
              navigate
            }

          />

        )}


      {/* ======================================================
          ERROR
      ====================================================== */}

      {currentRoute === 'error' &&
        currentError && (

          <ErrorView

            error={
              currentError
            }

            onRetry={
              handleRetryUpload
            }

            onBackToUpload={() => {

              setCurrentRoute(
                'upload'
              );

            }}

            onUploadDifferent={() => {

              setCurrentJob(
                null
              );

              setCurrentRoute(
                'upload'
              );

            }}

            onDownloadGlb={
              handleDownloadGlb
            }

          />

        )}


      {/* ======================================================
          FOOTER
      ====================================================== */}

      {currentRoute !== 'result' && (

        <Footer />

      )}

    </div>

  );

}