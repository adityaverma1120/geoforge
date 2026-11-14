"""
storage.py — Durable Storage Abstraction Layer for GeoForge

Provides dual-mode storage:
1. Local Filesystem (Default): Stores videos in backend/uploads and GLBs in backend/temp.
2. Cloud Object Storage (Supabase Storage / Cloudflare R2 / S3): Enabled when environment
   variables S3_ENDPOINT_URL or SUPABASE_URL are configured.
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("geoforge.storage")

BASE_DIR = Path(__file__).resolve().parent
LOCAL_UPLOAD_DIR = BASE_DIR / "uploads"
LOCAL_TEMP_DIR = BASE_DIR / "temp"
LOCAL_OUTPUT_DIR = BASE_DIR / "output"

for d in (LOCAL_UPLOAD_DIR, LOCAL_TEMP_DIR, LOCAL_OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Cloud Storage Configuration
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "geoforge-models")
S3_PUBLIC_DOMAIN = os.environ.get("S3_PUBLIC_DOMAIN")


def is_cloud_storage_enabled() -> bool:
    """Check whether cloud object storage is configured and enabled."""
    return bool(S3_ENDPOINT_URL and S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY)


def get_s3_client():
    """Create a boto3 S3 client for Cloudflare R2 or Supabase Storage."""
    if not is_cloud_storage_enabled():
        return None
    try:
        import boto3
        from botocore.config import Config
        return boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4")
        )
    except ImportError:
        logger.warning("boto3 is not installed; falling back to local filesystem storage.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize S3 storage client: {e}")
        return None


def store_uploaded_video(job_id: str, filename: str, temp_source_path: Path) -> str:
    """
    Store an uploaded video either in local uploads/ or remote object storage.
    Returns the resolved path or remote storage key/URI.
    """
    safe_name = Path(filename).name
    local_target = LOCAL_UPLOAD_DIR / f"{job_id}_{safe_name}"

    # Always ensure local copy exists for immediate processing
    if temp_source_path != local_target and temp_source_path.exists():
        shutil.copy2(temp_source_path, local_target)

    s3 = get_s3_client()
    if s3:
        try:
            key = f"uploads/{job_id}/{safe_name}"
            s3.upload_file(str(local_target), S3_BUCKET_NAME, key)
            logger.info(f"[{job_id}] Uploaded video persisted to remote object storage: {key}")
            return f"s3://{S3_BUCKET_NAME}/{key}"
        except Exception as e:
            logger.error(f"[{job_id}] Remote video upload failed, retaining local copy: {e}")

    return str(local_target)


def store_model_glb(job_id: str, local_glb_path: Path) -> Optional[str]:
    """
    Persist generated model.glb to remote object storage if configured.
    Returns the public/signed URL or None if local.
    """
    if not local_glb_path.exists():
        return None

    s3 = get_s3_client()
    if s3:
        try:
            key = f"models/{job_id}/model.glb"
            s3.upload_file(
                str(local_glb_path),
                S3_BUCKET_NAME,
                key,
                ExtraArgs={"ContentType": "model/gltf-binary"}
            )
            logger.info(f"[{job_id}] Generated GLB persisted to remote object storage: {key}")
            if S3_PUBLIC_DOMAIN:
                return f"{S3_PUBLIC_DOMAIN.rstrip('/')}/{key}"
            return f"{S3_ENDPOINT_URL.rstrip('/')}/{S3_BUCKET_NAME}/{key}"
        except Exception as e:
            logger.error(f"[{job_id}] Failed to push GLB to remote storage: {e}")

    return None

