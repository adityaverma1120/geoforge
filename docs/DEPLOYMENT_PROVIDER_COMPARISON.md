# Cloud Deployment Provider Comparison & Service Selection Matrix — GeoForge

> **Document:** `DEPLOYMENT_PROVIDER_COMPARISON.md`  
> **Status:** Comparative Evaluation Specification (Phase 8 Planning)  
> **Target Version:** GeoForge v1.1.0 Cloud Architecture  
> **Author:** Antigravity Engineering Team  
> **Last Verified:** 2026-11-14  
> **Related Documents:** [`docs/PHASE_8_DEPLOYMENT_STRATEGY.md`](PHASE_8_DEPLOYMENT_STRATEGY.md), [`docs/CLOUD_ARCHITECTURE.md`](CLOUD_ARCHITECTURE.md), [`docs/CLOUD_COST_ESTIMATES.md`](CLOUD_COST_ESTIMATES.md)

---

## 1. Evaluation Methodology

To identify the most practical, reliable, and cost-effective cloud infrastructure for GeoForge, 14 major cloud services were benchmarked across the five foundational layers of the system:
1. **Frontend Static Hosting:** Serving the React 19 / Three.js SPA.
2. **Backend API Hosting:** Running the FastAPI ASGI server and request orchestrator.
3. **Database & State:** Storing reconstruction records, timestamps, and stage logs.
4. **Object Storage:** Storing raw uploaded videos, generated GLB models, and telemetry JSON files.
5. **Reconstruction GPU Compute:** Executing OpenCV, CUDA-accelerated COLMAP, and Open3D.

Each provider was evaluated on six objective criteria:
- **Free-Tier Viability:** What features are available at $0.00 without immediate billing lockouts.
- **Official Pricing:** Real rates as published on official pricing pages (verified November 2026).
- **Persistent Storage:** Native volume support or durability guarantees.
- **GPU Availability:** Access to NVIDIA CUDA hardware ($\ge 6.0\text{ Compute Capability}$).
- **Deployment Complexity:** Architectural overhead, DevOps effort, and container setup friction.
- **Stage Fit:** Practical suitability for an independent project seeking public accessibility without enterprise bloat.

---

## 2. Tier 1 — Frontend Static Hosting Providers

| Provider | Core Capability | Free-Tier Inclusions | Paid Pricing | Bandwidth Limits | GeoForge Suitability |
|---|---|---|---|---|---|
| **Cloudflare Pages** | Edge Git-integrated static site hosting | **Unlimited bandwidth**, 500 builds/mo, 1 concurrent build, unlimited sites | $20/mo (Pro: 5,000 builds/mo, advanced analytics) | **Unlimited free egress** | **WINNER (Best Fit)** |
| **Vercel** | Edge Next.js & Vite SPA platform | 100 GB bandwidth/mo, 6,000 build minutes/mo | $20/user/mo (Pro: 1 TB bandwidth, $40/100GB overage) | 100 GB/mo (Overage fees apply) | **Strong Alternative** |
| **Netlify** | Jamstack static platform | 100 GB bandwidth/mo, 300 build minutes/mo | $19/user/mo (Pro: 1 TB bandwidth) | 100 GB/mo ($55/100GB overage) | **Viable Alternative** |

### Analysis & Verdict:
- **Cloudflare Pages** is the clear winner for GeoForge. Unlike Vercel and Netlify which enforce strict 100 GB bandwidth ceilings on free tiers, Cloudflare Pages provides **unlimited data transfer** with global Anycast CDN caching. For heavy WebGL applications delivering multi-megabyte JavaScript chunks, zero egress bandwidth billing guarantees no surprise charges.
- **Vercel** is an excellent alternative if seamless GitHub pull-request preview environments are desired.

---

## 3. Tier 2 — Backend API Hosting Providers (CPU Workloads)

| Provider | Service Type | Free-Tier Limits | Paid Pricing (Baseline) | Persistent Disk | GeoForge Suitability |
|---|---|---|---|---|---|
| **Railway** | Container PaaS with persistent volume | $5 one-time trial; $1/mo free credit | **$5/mo base (Hobby)** + $0.00000772/vCPU-s + $0.00000386/GB-s | **Yes** ($0.15/GB-mo volume) | **WINNER (PaaS)** |
| **Hetzner Cloud** | Unmanaged Linux VPS (x86 / ARM) | None | **€4.49/mo** (~$4.85/mo for CX23: 2 vCPU, 4 GB RAM, 40 GB NVMe) | **Yes** (40 GB NVMe included) | **WINNER (VPS)** |
| **Render** | Managed container Web Service | Free tier sleeps after 15m inactivity; 50s spin-up | $7/mo (Starter: 0.5 vCPU, 512 MB RAM); $25/mo for 1 GB RAM | Yes ($0.25/GB-mo paid) | **Acceptable** (Slow cold starts) |
| **DigitalOcean** | Basic Droplet (Ubuntu VPS) | $200 trial credit (60 days) | $4/mo (0.5 GB RAM, 1 vCPU) / $6/mo (1 GB RAM, 25 GB SSD) | Yes (Included NVMe) | **Strong Alternative** |

### Analysis & Verdict:
- **Railway:** Best for zero-maintenance PaaS deployment. Supports native Dockerfile deployments, automated SSL, GitHub triggers, and critically **supports persistent volumes** ($0.15/GB/mo), allowing SQLite `jobs.db` to survive container rebuilds without configuring a separate database server.
- **Hetzner Cloud (CX23):** Best price-to-performance ratio in the industry (€4.49/mo for 2 dedicated vCPUs, 4 GB RAM, 40 GB NVMe). Ideal if a dedicated virtual machine with Nginx is preferred.
- **Render:** Free tier is unsuitable because it automatically sleeps after 15 minutes of inactivity; waking the instance takes 50+ seconds, degrading user experience.

---

## 4. Tier 3 — Database & State Providers

| Provider | Technology | Free Tier | Paid Pricing | Automatic Backups | GeoForge Suitability |
|---|---|---|---|---|---|
| **Persistent SQLite** | Embedded SQLite 3 (`jobs.db`) | Included in disk storage | $0.00 (Zero hosting overhead) | Simple file copy / snapshot | **WINNER (Stage 8A / Simplest)** |
| **Supabase** | Managed PostgreSQL 15 | **500 MB database**, 50,000 monthly active users | $25/mo (Pro: 8 GB database, point-in-time recovery) | Daily automated backups | **WINNER (Stage 8B / Decoupled)** |
| **Neon** | Serverless PostgreSQL | 0.5 GB storage, autosuspend when idle | $19/mo (Launch: 10 GB storage, branching) | Point-in-time restore | **Strong Alternative** |
| **AWS RDS** | Managed Aurora / Postgres | 750 hours t4g.micro for 12 months (Free Tier) | ~$15–$30/mo baseline | Automated snapshots | **Overkill for current stage** |

### Analysis & Verdict:
- **Persistent SQLite (via Railway Volume or Hetzner VPS):** The simplest initial path. Requires **zero code changes**, preserves the existing 14-column schema in `backend/database.py`, and has zero monthly database SaaS cost.
- **Supabase (PostgreSQL):** The recommended decoupled database. Its generous free tier (500 MB) easily stores over 500,000 reconstruction job records. If multiple API instances or remote workers need to write job updates concurrently, Supabase solves connection concurrency cleanly.

---

## 5. Tier 4 — Object Storage Providers (Uploads & 3D Deliverables)

| Provider | API Compatibility | Free Tier | Storage Pricing (per GB/mo) | Data Egress (Bandwidth Out) | GeoForge Suitability |
|---|---|---|---|---|---|
| **Cloudflare R2** | S3-Compatible | **10 GB free storage**, 1M Class A, 10M Class B ops | **$0.015 / GB** | **$0.00 / GB (100% FREE EGRESS)** | **WINNER (Decisive)** |
| **AWS S3** | Native S3 | 5 GB for 12 months | $0.023 / GB | **$0.09 / GB (Extremely expensive egress)** | **Poor (High egress penalties)** |
| **Backblaze B2** | S3-Compatible | 10 GB free | $0.006 / GB | Free to Cloudflare / $0.01/GB | **Good Backup** |
| **DigitalOcean Spaces** | S3-Compatible | None | $5/mo (Includes 250 GB storage & 1 TB egress) | $0.01 / GB overage | **Acceptable** |

### Analysis & Verdict:
- **Cloudflare R2 is the indisputable choice for GeoForge.** Drone videos (50–500 MB) and 3D GLBs (5–25 MB) involve heavy file transfer. On AWS S3, streaming or downloading 1 TB of models costs **$90.00 in bandwidth fees alone**. Cloudflare R2 charges **$0.00 for data egress**, permanently eliminating bandwidth penalties.

---

## 6. Tier 5 — Reconstruction GPU Compute Providers

This is the most critical technical and economic decision in the GeoForge architecture.

| Provider | GPU Model & VRAM | Billing Model | Hourly Rate | Cost for 4.4-min Job | Idle Cost | GeoForge Suitability |
|---|---|---|---|---|---|---|
| **RunPod (Serverless)** | NVIDIA RTX 4000 / A4000 (16 GB) | Per-second execution | **$0.58 / active hr** | **~$0.043 (₹4.00)** | **$0.00** | **WINNER (Production Decoupled)** |
| **RunPod (Community Pod)** | NVIDIA RTX 3070 / 3080 (8–10 GB) | Per-second pod runtime | **$0.13 – $0.22 / hr** | ~$0.012 (when active) | $0.005/hr (storage when stopped) | **WINNER (Staging Prototype)** |
| **Vast.ai** | Various (RTX 3070 to 4090) | Per-hour bid/on-demand | $0.10 – $0.25 / hr | ~$0.01 | $0.00 when destroyed | **High friction (P2P reliability risks)** |
| **AWS EC2 (`g4dn.xlarge`)** | NVIDIA T4 (16 GB) | On-demand / 1-second | $0.526 / hr | ~$0.04 | **$378/mo if left running 24/7** | **Expensive if always-on** |
| **GCP (`g2-standard-4`)** | NVIDIA L4 (24 GB) | On-demand / 1-second | $0.70 / hr | ~$0.05 | **$504/mo if left running 24/7** | **Expensive if always-on** |
| **Lambda Cloud** | NVIDIA A10 (24 GB) | Hourly | $0.50 / hr | ~$0.037 | $0.00 when destroyed | **Availability issues (frequent shortages)** |

### Analysis & Verdict:
- **RunPod Serverless GPU:** Best for scalable public deployment. Containers scale from zero instances up on-demand when a reconstruction job is submitted. It bills strictly for active compute time ($0.00016/sec = ~$0.04 per reconstruction). When no users are reconstructing, the compute bill is **$0.00**.
- **RunPod Community Pod:** Best for initial prototype verification. A dedicated pod with an RTX 3070 (8 GB VRAM) costs only **$0.13/hour**. It can be started manually for testing sessions and stopped immediately after, incurring only ~$0.005/hour for persistent volume storage.

---

## 7. Recommended Architecture Stacks

### 7.1 Primary Recommended Stack (The Sustainable Cloud Architecture)
- **Frontend:** Cloudflare Pages (Free, Unlimited Bandwidth)
- **Backend API:** Railway Hobby ($5.00/mo baseline credit)
- **Database:** Supabase PostgreSQL (Free tier, 500 MB storage)
- **Object Storage:** Cloudflare R2 (10 GB free, $0.00 egress)
- **Reconstruction Worker:** RunPod Serverless GPU ($0.58/active hr = ~$0.04/job)
- **Total Fixed Monthly Cost:** **$5.00 / month ($\approx ₹425\text{--}₹470\text{/month}$)**

### 7.2 Secondary Prototype Stack (The Fast Staging Architecture)
- **Unified Host:** RunPod Dedicated GPU Pod (RTX 3070 8 GB, 20 GB Disk)
- **Setup:** RunPod container running Ubuntu 22.04 + CUDA + COLMAP + FastAPI + compiled React frontend on a single port via Nginx / FastAPI.
- **Workflow:** Started via script/dashboard before testing sessions; stopped when finished.
- **Total Cost:** **$0.13 / active hour** + **$1.50 / month** volume disk storage.

