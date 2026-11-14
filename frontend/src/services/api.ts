import { UploadResponse } from '../types';

/**
 * GeoForge API Service Layer
 *
 * FastAPI backend:
 * http://127.0.0.1:8000
 */

export const API_BASE_URL: string =
  (typeof import.meta !== 'undefined' &&
    (import.meta as any).env?.VITE_API_URL) ||
  'http://127.0.0.1:8000';


export interface UploadProgressCallback {
  (
    progress: {
      loaded: number;
      total: number;
      percentage: number;
    }
  ): void;
}


/**
 * ============================================================
 * UPLOAD DRONE VIDEO
 * ============================================================
 *
 * Sends:
 *
 * POST /upload
 *
 * FastAPI expects:
 *
 * file: UploadFile
 */
export async function uploadDroneVideo(
  file: File,
  onProgress?: UploadProgressCallback
): Promise<UploadResponse> {

  const url =
    `${API_BASE_URL.replace(/\/+$/, '')}/upload`;

  const formData = new FormData();

  formData.append(
    'file',
    file,
    file.name
  );


  return new Promise(
    (resolve, reject) => {

      const xhr =
        new XMLHttpRequest();


      xhr.open(
        'POST',
        url,
        true
      );


      /**
       * ======================================================
       * UPLOAD PROGRESS
       * ======================================================
       */

      if (
        xhr.upload &&
        onProgress
      ) {

        xhr.upload.onprogress =
          (event) => {

            if (
              event.lengthComputable
            ) {

              const percentage =
                Math.round(
                  (
                    event.loaded /
                    event.total
                  ) * 100
                );


              onProgress({
                loaded:
                  event.loaded,

                total:
                  event.total,

                percentage
              });

            }

          };

      }


      /**
       * ======================================================
       * RESPONSE
       * ======================================================
       */

      xhr.onload = () => {

        if (
          xhr.status >= 200 &&
          xhr.status < 300
        ) {

          try {

            const jsonResponse:
              UploadResponse =
              JSON.parse(
                xhr.responseText
              );

            resolve(
              jsonResponse
            );

          } catch {

            resolve({
              status:
                'success',

              message:
                xhr.responseText ||
                'Video uploaded successfully',

              job_id:
                `GF-${Date.now()
                  .toString(36)
                  .toUpperCase()}`
            });

          }

          return;
        }


        /**
         * ====================================================
         * BACKEND ERROR
         * ====================================================
         */

        let errorData: any = {};


        try {

          errorData =
            JSON.parse(
              xhr.responseText
            );

        } catch {

          errorData = {
            message:
              xhr.statusText ||
              `HTTP ${xhr.status}`
          };

        }


        const error =
          new Error(
            errorData.detail ||
            errorData.message ||
            `Upload failed with HTTP ${xhr.status}`
          ) as Error & {
            status?: number;
            response?: any;
          };


        error.status =
          xhr.status;

        error.response =
          errorData;


        reject(error);

      };


      /**
       * ======================================================
       * NETWORK ERROR
       * ======================================================
       */

      xhr.onerror = () => {

        const error =
          new Error(
            'Reconstruction server is unavailable or network error occurred.'
          ) as Error & {
            isNetworkError?: boolean;
          };


        error.isNetworkError =
          true;


        reject(error);

      };


      /**
       * ======================================================
       * TIMEOUT
       * ======================================================
       */

      xhr.ontimeout = () => {

        const error =
          new Error(
            'Upload request timed out.'
          ) as Error & {
            isTimeout?: boolean;
          };


        error.isTimeout =
          true;


        reject(error);

      };


      /**
       * ======================================================
       * SEND REQUEST
       * ======================================================
       */

      xhr.send(
        formData
      );

    }
  );

}


/**
 * ============================================================
 * JOB STATUS
 * ============================================================
 *
 * GET /status/{job_id}
 *
 * Returns: { status: 'queued'|'processing'|'complete'|'failed', filename, result?, error? }
 */
export async function getJobStatus(
  jobId: string
): Promise<any> {

  const url =
    `${API_BASE_URL.replace(/\/+$/, '')}/status/${encodeURIComponent(jobId)}`;

  const response = await fetch(url);

  if (!response.ok) {
    const err = new Error(`Status check returned HTTP ${response.status}`) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }

  return await response.json();

}


/**
 * ============================================================
 * GLB MODEL URL
 * ============================================================
 *
 * FastAPI backend:
 *
 * GET /model/{job_id}
 *
 * This function accepts either:
 *
 * 1. A plain job ID:
 *    3c99d500-1fe8-4504-a5e6-8d129d2bbdea
 *
 * 2. A model path:
 *    /model/3c99d500-1fe8-4504-a5e6-8d129d2bbdea
 *
 * 3. A complete URL:
 *    http://127.0.0.1:8000/model/3c99d500-...
 *
 * It prevents the frontend from creating:
 *
 * /model//model/{job_id}
 */
export function getModelGlbUrl(
  jobIdOrUrl: string
): string {

  const value =
    jobIdOrUrl.trim();


  /**
   * ==========================================================
   * ALREADY A COMPLETE URL
   * ==========================================================
   */

  if (
    value.startsWith('http://') ||
    value.startsWith('https://') ||
    value.startsWith('blob:')
  ) {

    return value;

  }


  /**
   * ==========================================================
   * REMOVE DUPLICATED MODEL PATH
   * ==========================================================
   *
   * Example:
   *
   * /model/12345
   *
   * becomes:
   *
   * 12345
   */

  let jobId =
    value;


  if (
    jobId.startsWith('/model/')
  ) {

    jobId =
      jobId.substring(
        '/model/'.length
      );

  }


  /**
   * ==========================================================
   * REMOVE ACCIDENTAL SLASHES
   * ==========================================================
   */

  jobId =
    jobId.replace(
      /^\/+|\/+$/g,
      ''
    );


  /**
   * ==========================================================
   * FINAL FASTAPI MODEL URL
   * ==========================================================
   */

  return `${API_BASE_URL.replace(/\/+$/, '')}/model/${encodeURIComponent(jobId)}`;

}


/**
 * ============================================================
 * DOWNLOAD GLB URL
 * ============================================================
 */
export function getDownloadGlbUrl(jobId: string): string {
  const cleanId = jobId.replace(/^\/+|\/+$/g, '');
  return `${API_BASE_URL.replace(/\/+$/, '')}/download/${encodeURIComponent(cleanId)}`;
}


/**
 * ============================================================
 * GET BACKEND HEALTH
 * ============================================================
 */
export async function getHealth(): Promise<any> {
  const url = `${API_BASE_URL.replace(/\/+$/, '')}/health`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Health check returned HTTP ${response.status}`);
  }
  return await response.json();
}


/**
 * ============================================================
 * GET JOB METADATA MANIFEST
 * ============================================================
 *
 * GET /metadata/{job_id}
 */
export async function getJobMetadata(jobId: string): Promise<any> {
  const cleanId = jobId.replace(/^\/+|\/+$/g, '');
  const url = `${API_BASE_URL.replace(/\/+$/, '')}/metadata/${encodeURIComponent(cleanId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    const err = new Error(`Metadata fetch returned HTTP ${response.status}`) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }
  return await response.json();
}


/**
 * ============================================================
 * LIST PERSISTENT JOBS HISTORY
 * ============================================================
 *
 * GET /jobs?limit={limit}
 */
export async function listJobs(limit: number = 50): Promise<any[]> {
  const url = `${API_BASE_URL.replace(/\/+$/, '')}/jobs?limit=${encodeURIComponent(limit)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Jobs history fetch returned HTTP ${response.status}`);
  }
  return await response.json();
}


/**
 * ============================================================
 * CANCEL JOB
 * ============================================================
 *
 * POST /jobs/{job_id}/cancel
 */
export async function cancelJob(jobId: string): Promise<any> {
  const cleanId = jobId.replace(/^\/+|\/+$/g, '');
  const url = `${API_BASE_URL.replace(/\/+$/, '')}/jobs/${encodeURIComponent(cleanId)}/cancel`;
  const response = await fetch(url, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`Cancel job returned HTTP ${response.status}`);
  }
  return await response.json();
}


/**
 * ============================================================
 * DELETE / CANCEL JOB
 * ============================================================
 */
export async function deleteJob(jobId: string): Promise<any> {
  const url = `${API_BASE_URL.replace(/\/+$/, '')}/jobs/${encodeURIComponent(jobId)}`;
  const response = await fetch(url, { method: 'DELETE' });
  if (!response.ok) {
    throw new Error(`Delete job returned HTTP ${response.status}`);
  }
  return await response.json();
}
