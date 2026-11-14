-- ============================================================
-- GeoForge Historical Jobs Seed Data for Supabase
-- Generated from backend/jobs.db
-- ============================================================

INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    'd59c2670-8548-4e55-b8d9-e909ca8aa715', 'sample_drone_orbit.mp4', 'failed', 'sparse_quality_check', 55, 'Interrupted by server restart',
    'backend\uploads\d59c2670-8548-4e55-b8d9-e909ca8aa715_sample_drone_orbit.mp4', 'backend\temp\d59c2670-8548-4e55-b8d9-e909ca8aa715', '', NULL, 'Reconstruction was interrupted by a server restart. Please upload again.',
    '2026-11-11T12:01:06.811444+00:00', '2026-11-11T12:17:00.482937+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    '00caf7d6-7504-4e30-b469-5e0eeefe4331', 'sample_drone_orbit.mp4', 'failed', 'sparse_quality_check', 55, 'Interrupted by server restart',
    'backend\uploads\00caf7d6-7504-4e30-b469-5e0eeefe4331_sample_drone_orbit.mp4', 'backend\temp\00caf7d6-7504-4e30-b469-5e0eeefe4331', '', NULL, 'Reconstruction was interrupted by a server restart. Please upload again.',
    '2026-11-11T12:11:11.979421+00:00', '2026-11-11T12:17:00.482937+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    'e5543b4c-2369-4461-8112-b31ed4f87ff3', 'sample_drone_orbit.mp4', 'failed', 'dense_stereo', 70, 'Interrupted by server restart',
    'backend\uploads\e5543b4c-2369-4461-8112-b31ed4f87ff3_sample_drone_orbit.mp4', 'backend\temp\e5543b4c-2369-4461-8112-b31ed4f87ff3', '', NULL, 'Reconstruction was interrupted by a server restart. Please upload again.',
    '2026-11-11T12:17:00.625994+00:00', '2026-11-11T12:30:39.103125+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    'dda15414-1842-4633-b013-b91e84564d5f', 'sample_drone_orbit.mp4', 'complete', 'completed', 100, 'Reconstruction complete!',
    'backend\uploads\dda15414-1842-4633-b013-b91e84564d5f_sample_drone_orbit.mp4', 'backend\temp\dda15414-1842-4633-b013-b91e84564d5f', 'backend\temp\dda15414-1842-4633-b013-b91e84564d5f\colmap\textured\model.glb', '{"model_path": "backend\\temp\\dda15414-1842-4633-b013-b91e84564d5f\\colmap\\textured\\model.glb", "model_url": "/model/dda15414-1842-4633-b013-b91e84564d5f", "download_url": "/download/dda15414-1842-4633-b013-b91e84564d5f", "glb_size_mb": 1.55, "frames_extracted": 30, "frames_used": 30, "pipeline_status": "complete"}'::jsonb, NULL,
    '2026-11-11T12:30:39.260399+00:00', '2026-11-11T12:35:10.520372+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    'a51cff28-b55b-4061-ae32-45370bc1ece8', 'unit_test_sample.mp4', 'failed', 'failed', 15, 'Reconstruction failed: Only 3 frames passed filtering. At least 20 are needed for a useful reconstruction. Try uploading a longer video or reducing the sharpness threshold.',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\a51cff28-b55b-4061-ae32-45370bc1ece8_unit_test_sample.mp4', 'backend\temp\a51cff28-b55b-4061-ae32-45370bc1ece8', '', NULL, 'Only 3 frames passed filtering. At least 20 are needed for a useful reconstruction. Try uploading a longer video or reducing the sharpness threshold.',
    '2026-11-11T13:39:39.432034+00:00', '2026-11-11T13:39:39.530096+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    'be844c83-0a3e-4716-8dcf-459d141a0161', 'busy_test.mp4', 'failed', 'failed', 0, 'Server at capacity',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\be844c83-0a3e-4716-8dcf-459d141a0161_busy_test.mp4', 'backend\temp\be844c83-0a3e-4716-8dcf-459d141a0161', '', NULL, 'Server is at capacity (1 jobs running). Please try again shortly.',
    '2026-11-11T13:40:21.350135+00:00', '2026-11-11T13:40:21.354089+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    '93248cc9-769e-43c9-a4fd-4884f6e12dfc', 'busy_test.mp4', 'failed', 'failed', 0, 'Server at capacity',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\93248cc9-769e-43c9-a4fd-4884f6e12dfc_busy_test.mp4', 'C:\Users\adity\Downloads\geoforge-main\backend\temp\93248cc9-769e-43c9-a4fd-4884f6e12dfc', '', NULL, 'Server is at capacity (1 jobs running). Please try again shortly.',
    '2026-11-11T13:58:48.246406+00:00', '2026-11-11T13:58:48.250800+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    '2f905360-b054-47a6-acae-9252eeb71142', 'busy_test.mp4', 'failed', 'failed', 0, 'Server at capacity',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\2f905360-b054-47a6-acae-9252eeb71142_busy_test.mp4', 'C:\Users\adity\Downloads\geoforge-main\backend\temp\2f905360-b054-47a6-acae-9252eeb71142', '', NULL, 'Server is at capacity (1 jobs running). Please try again shortly.',
    '2026-11-11T14:59:42.271600+00:00', '2026-11-11T14:59:42.276209+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    'e6a72be4-dfaa-4273-ace2-99f0a3083066', 'sample_drone_orbit.mp4', 'failed', 'extracting_features', 35, 'Interrupted by server restart',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\e6a72be4-dfaa-4273-ace2-99f0a3083066_sample_drone_orbit.mp4', 'C:\Users\adity\Downloads\geoforge-main\backend\temp\e6a72be4-dfaa-4273-ace2-99f0a3083066', '', NULL, 'Reconstruction was interrupted by a server restart. Please upload again.',
    '2026-11-11T15:15:00.950030+00:00', '2026-11-12T13:45:28.699534+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    '14da84d2-92aa-48c4-beaf-29b2ec68f54e', 'unit_test_sample.mp4', 'failed', 'failed', 0, 'Server at capacity',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\14da84d2-92aa-48c4-beaf-29b2ec68f54e_unit_test_sample.mp4', 'C:\Users\adity\Downloads\geoforge-main\backend\temp\14da84d2-92aa-48c4-beaf-29b2ec68f54e', '', NULL, 'Server is at capacity (1 jobs running). Please try again shortly.',
    '2026-11-12T13:44:50.126376+00:00', '2026-11-12T13:44:50.130656+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    '07be49ba-078d-462d-bcf7-8bd16995044b', 'busy_test.mp4', 'failed', 'failed', 0, 'Server at capacity',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\07be49ba-078d-462d-bcf7-8bd16995044b_busy_test.mp4', 'C:\Users\adity\Downloads\geoforge-main\backend\temp\07be49ba-078d-462d-bcf7-8bd16995044b', '', NULL, 'Server is at capacity (1 jobs running). Please try again shortly.',
    '2026-11-12T13:46:30.776488+00:00', '2026-11-12T13:46:30.782341+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    '00b99ffd-4c6d-45bc-9ae2-13017d411ff3', 'acceptance_test_orbit.mp4', 'complete', 'completed', 100, 'Reconstruction completed successfully!',
    'C:\Users\adity\Downloads\geoforge-main\backend\uploads\00b99ffd-4c6d-45bc-9ae2-13017d411ff3_acceptance_test_orbit.mp4', 'C:\Users\adity\Downloads\geoforge-main\backend\temp\00b99ffd-4c6d-45bc-9ae2-13017d411ff3', 'C:\Users\adity\Downloads\geoforge-main\backend\temp\00b99ffd-4c6d-45bc-9ae2-13017d411ff3\colmap\textured\model.glb', '{"model_path": "C:\\Users\\adity\\Downloads\\geoforge-main\\backend\\temp\\00b99ffd-4c6d-45bc-9ae2-13017d411ff3\\colmap\\textured\\model.glb", "model_url": "/model/00b99ffd-4c6d-45bc-9ae2-13017d411ff3", "download_url": "/download/00b99ffd-4c6d-45bc-9ae2-13017d411ff3", "metadata_url": "/metadata/00b99ffd-4c6d-45bc-9ae2-13017d411ff3", "glb_size_mb": 4.1, "frames_extracted": 30, "frames_used": 30, "num_sparse_points": 4446, "num_cameras": 1, "num_registered_images": 30, "warnings": ["Reconstruction fragmented into 2 components. Only the largest component is used."]}'::jsonb, NULL,
    '2026-11-14T12:05:24.302369+00:00', '2026-11-14T12:09:49.109821+00:00', NULL
) ON CONFLICT (job_id) DO NOTHING;
