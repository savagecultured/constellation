
# 📡 Streaming Platform — System Architecture (v1.1)

## Overview

This platform is a **freemium-driven media streaming service** engineered for **controlled growth**. It prioritizes **cost-efficiency, deterministic performance, and incremental scalability**—starting from a single-node deployment and evolving into a distributed cluster.

Initial capacity targets:

- ~20 concurrent users
- چند terabytes of media storage
- Single-node infrastructure with forward compatibility for clustering

---

## 🧱 Tech Stack

- **Frontend:** Next.js
- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Cache / Quota Engine:** Redis
- **Video / Podcasts:** Jellyfin
- **Music / Audiobooks:** Navidrome
- **Payments:** Payoneer
- **Email Delivery:** Mailgun

---

## 🏗️ Deployment Strategy

### Phase 0: Single-Node (Initial State)

**Host:** Proxmox (or equivalent hypervisor)  
**Topology:** Consolidated but logically segmented

|Layer|Deployment Model|
|---|---|
|Frontend (Next.js)|Container (Node runtime)|
|Backend (FastAPI)|Container (Uvicorn/Gunicorn)|
|PostgreSQL|Dedicated container or VM|
|Redis|Lightweight container|
|Jellyfin|LXC / VM (GPU optional)|
|Navidrome|Container|
|Nginx|Reverse proxy (entry point)|

**Storage Strategy:**

- Single mounted volume (`/mnt/media`)
- Structured directories:
    - `/video`
    - `/music`
    - `/podcasts`

**Reality check:**  
At 20 concurrent users, this setup will hold—provided you avoid unnecessary transcoding.

---

### Phase 1: Vertical Scaling

Before clustering, extract maximum value from the node:

- Enable hardware transcoding (if GPU/QuickSync available)
- Tune PostgreSQL (shared_buffers, work_mem)
- Introduce read caching (Redis-backed metadata)
- Optimize disk I/O (ZFS or SSD-backed storage)

---

### Phase 2: Horizontal Expansion (Cluster)

When limits are reached:

- Split services:
    - Media servers → dedicated nodes
    - Database → isolated instance with replication
    - Backend → replicated API instances
- Introduce:
    - Load balancer (HAProxy / Nginx)
    - Distributed storage (Ceph or NFS with caution)

---

## 🏗️ Architectural Layers

### 1. Client Tier

Next.js handles:

- Public access
- Auth flows
- Media playback UI
- Subscription management
- Admin interface

**Strict rule:**  
No direct access to media services—everything flows through the backend.

---

### 2. API Gateway (FastAPI)

The system’s **control plane**.

Responsibilities:

- JWT authentication
- Request validation
- Quota enforcement
- Service orchestration

---

### 3. Core Services

#### 🔁 Stream Proxy

- Validates subscription tier
- Enforces concurrent stream limits
- Issues **short-lived signed tokens**
- Routes traffic to:
    - Jellyfin
    - Navidrome

**Design stance:**

- Never expose upstream media endpoints
- Tokens expire aggressively (≤ 60 seconds)

---

#### 💳 Subscription Manager

- Integrates with Payoneer
- Handles:
    - Billing lifecycle
    - Tier transitions
    - Grace periods

**Webhook pipeline:**

- Idempotent processing (non-negotiable)
- Retry-safe architecture

---

#### 🛠️ Admin API

- Media ingestion workflows
- User moderation
- Platform analytics

---

## 🗄️ Data Architecture

### PostgreSQL

Authoritative store for:

- Users
- Subscriptions
- Media metadata
- Stream history

**Operational stance:**

- Daily backups (automated)
- WAL archiving for recovery

---

### Redis

Handles:

- Active stream tracking
- Monthly quota counters

**Implementation detail:**

- Keys structured as:
    
    stream:{user_id}:{month}
    
- TTL aligned with calendar month rollover

---

## 🔌 External Integrations

### Media Layer

- Jellyfin → video/podcasts
- Navidrome → music/audiobooks

---

### Payments

- Payoneer for billing workflows
- Webhooks drive subscription state

---

### Email Infrastructure

- Mailgun for:
    - Receipts
    - Renewal reminders
    - Alerts

---

## 🌐 Self-Hosted Edge Strategy

You’ve opted out of third-party CDNs. That’s fine—but it comes with responsibility.

### Edge Layer (Nginx)

Responsibilities:

- TLS termination
- Static asset caching
- Reverse proxy routing

### Optimization Tactics:

- Enable byte-range requests (critical for streaming)
- Cache static frontend assets aggressively
- Use pre-signed URLs for controlled media delivery
- Apply gzip/brotli for API responses

**Hard truth:**  
Without a global CDN, latency will scale poorly across regions. Acceptable at your current scale, not at global expansion.

---

## 🚀 Development Roadmap (Refined)

### Phase 1 — Foundation

- Auth system (JWT + OAuth)
- DB schema + migrations
- Admin baseline
- CI/CD pipeline

---

### Phase 2 — Streaming Core

- Media server integration
- Stream proxy (critical path)
- Redis quota enforcement
- Player UI

---

### Phase 3 — Monetization

- Payoneer integration
- Subscription lifecycle engine
- Mailgun notifications
- Conversion funnel

---

### Phase 4 — Hardening & Launch

- Upload + sync workflows
- Analytics dashboard
- Security:
    - Rate limiting
    - Token expiry enforcement
- Performance tuning
- Dockerized deployment behind Nginx

---

## 🔐 Security Model

- JWT-based authentication
- Short-lived stream tokens
- No direct media server exposure
- Rate limiting on all endpoints
- Input sanitization

---

## 📈 Capacity Planning (Reality-Based)

|Resource|Expectation|
|---|---|
|CPU|Moderate (spikes during transcoding)|
|RAM|16–32GB recommended|
|Storage|3–10TB initial|
|Network|Bottleneck if streaming remotely|

---

## ⚠️ Known Constraints

- Single-node = single point of failure
- Redis loss = temporary quota inconsistency
- Payoneer webhook delays = subscription lag
- No CDN = regional performance limitations

---

## 📌 Strategic Direction

This system is deliberately:

- **Lean at inception**
- **Modular by design**
- **Ready for scale—but not prematurely over-engineered**


/home/nebula/Documents/Obsidian/Plan.md