# 18 — Deployment and operations

## Current development model
Frontend and backend are separate services. Vite development server runs on port 3000; FastAPI commonly runs on port 8000. The frontend default API address is loopback, which is appropriate for local development only.

## Deployment considerations
- Set `VITE_API_URL` to a reachable backend URL at frontend build time.
- Set `ALLOWED_ORIGINS` to exact deployed frontend origins.
- Set `COLMAP_EXE` to a valid executable path and ensure all required assets are accessible.
- Ensure backend upload/temp/output paths are writable and have sufficient capacity.
- Configure reverse-proxy request size and timeout limits consistently with backend upload limits.
- Long-running reconstruction may exceed default proxy/request timeouts; asynchronous job polling is the current pattern.
- Use persistent storage and durable job queue if jobs must survive restarts.
- Add authentication, rate limiting, monitoring, structured logs, and resource isolation before internet-facing deployment.

## Deployment status
The supplied archive does not prove that a production deployment, container setup, CI/CD pipeline, or cloud storage integration is configured.
