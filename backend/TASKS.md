# Backend Development Tasks

## Phase 1 — Foundation

### 1.1 Auth System (JWT + OAuth)

- [x] Set up FastAPI project structure with app initialization
- [x] Create JWT token generation utility in [`app/core/security.py`](app/core/security.py)
- [x] Implement token validation middleware
- [x] Add JWT refresh token endpoint
- [x] Set up OAuth2 password flow
- [x] Create login/logout endpoints in [`app/api/v1/auth.py`](app/api/v1/auth.py)
- [x] Add token expiration handling

### 1.2 DB Schema + Migrations

- [x] Define SQLAlchemy models in [`app/models/user.py`](app/models/user.py)
- [x] Create database configuration in [`app/core/config.py`](app/core/config.py)
- [x] Set up connection pool in [`app/core/database.py`](app/core/database.py)
- [x] Write Alembic migration scripts
- [x] Create initial migration for users table
- [x] Add indexes for performance
- [x] Verify migration rollback capability

### 1.3 Admin Baseline

- [x] Create user management endpoints in [`app/api/v1/admin.py`](app/api/v1/admin.py)
- [x] Implement user CRUD operations
- [x] Add admin authentication middleware
- [x] Create user search/filter functionality
- [x] Build admin dashboard data endpoints

### 1.4 CI/CD Pipeline

- [x] Set up GitHub Actions workflow in `.github/`
- [x] Configure automated testing
- [x] Add linting (flake8/ruff)
- [x] Set up type checking (mypy)
- [x] Configure Docker build automation
- [x] Set up automated deployment triggers

---

## Phase 2 — Streaming Core

### 2.1 Media Server Integration

- [x] Create Jellyfin API client wrapper
- [x] Create Navidrome API client wrapper
- [x] Implement media library fetch endpoints
- [x] Add media search functionality
- [x] Set up media metadata sync job
- [x] Configure API timeout handling

### 2.2 Stream Proxy (Critical Path)

- [ ] Design stream proxy architecture
- [ ] Implement subscription tier validation
- [ ] Add concurrent stream limit enforcement
- [ ] Create short-lived signed token generator (≤60s expiry)
- [ ] Build traffic routing logic to Jellyfin/Navidrome
- [ ] Implement token validation middleware
- [ ] Add stream analytics tracking

### 2.3 Redis Quota Enforcement

- [ ] Set up Redis connection in [`app/core/config.py`](app/core/config.py)
- [ ] Design quota key structure: `stream:{user_id}:{month}`
- [ ] Implement monthly quota counter
- [ ] Add TTL management aligned with calendar month
- [ ] Create quota check middleware
- [ ] Implement quota consumption logic
- [ ] Add quota reset handling

### 2.4 Player UI Backend

- [ ] Create stream playback endpoints
- [ ] Implement media transcoding request handling
- [ ] Add playlist generation (HLS/DASH)
- [ ] Build stream session management
- [ ] Implement pause/resume functionality

---

## Phase 3 — Monetization

### 3.1 Payoneer Integration

- [ ] Set up Payoneer API client
- [ ] Create webhook endpoint for payment events
- [ ] Implement webhook signature validation
- [ ] Add idempotent processing logic
- [ ] Build retry-safe architecture
- [ ] Create payment status sync job

### 3.2 Subscription Lifecycle Engine

- [ ] Design subscription state machine
- [ ] Implement tier management
- [ ] Add grace period handling
- [ ] Create subscription upgrade/downgrade flow
- [ ] Implement trial period logic
- [ ] Add subscription expiration alerts

### 3.3 Mailgun Notifications

- [ ] Set up Mailgun API client
- [ ] Create notification templates
- [ ] Implement receipt emails
- [ ] Build renewal reminder system
- [ ] Add alert notification system
- [ ] Configure email queue processing

### 3.4 Conversion Funnel

- [ ] Create signup flow endpoints
- [ ] Implement trial-to-paid conversion
- [ ] Add payment method storage
- [ ] Build invoice generation
- [ ] Implement discount code system

---

## Phase 4 — Hardening & Launch

### 4.1 Upload + Sync Workflows

- [ ] Create media upload endpoint
- [ ] Implement chunked upload handling
- [ ] Add upload progress tracking
- [ ] Build media library sync job
- [ ] Implement file validation
- [ ] Add metadata extraction

### 4.2 Analytics Dashboard

- [ ] Design analytics data models
- [ ] Create usage tracking endpoints
- [ ] Implement stream history logging
- [ ] Build user activity aggregation
- [ ] Create dashboard API endpoints
- [ ] Add export functionality

### 4.3 Security

- [ ] Implement rate limiting middleware
- [ ] Add token expiry enforcement
- [ ] Configure CORS policies
- [ ] Add request size limits
- [ ] Implement SQL injection protection
- [ ] Add XSS protection headers

### 4.4 Performance Tuning

- [ ] Optimize PostgreSQL queries
- [ ] Add database connection pooling
- [ ] Implement Redis caching strategy
- [ ] Profile API endpoints
- [ ] Add query result caching

### 4.5 Dockerized Deployment

- [ ] Create production Dockerfile
- [ ] Configure uvicorn/gunicorn workers
- [ ] Set up Nginx reverse proxy
- [ ] Configure environment variables
- [ ] Add health check endpoints
- [ ] Set up log rotation
- [ ] Configure graceful shutdown

---

## Data Architecture Tasks

### PostgreSQL Tasks

- [ ] Configure `shared_buffers` and `work_mem`
- [ ] Set up daily automated backups
- [ ] Configure WAL archiving
- [ ] Create backup recovery procedure
- [ ] Set up read replicas (Phase 2)

### Redis Tasks

- [ ] Configure persistence
- [ ] Set up cluster mode preparation
- [ ] Implement key expiration monitoring
- [ ] Add memory management

---

## External Integration Tasks

### Media Layer

- [ ] Configure Jellyfin connection
- [ ] Configure Navidrome connection
- [ ] Set up media server health checks

### Payments

- [ ] Set up Payoneer sandbox
- [ ] Configure webhook retry logic
- [ ] Add payment reconciliation

### Email

- [ ] Configure Mailgun domain
- [ ] Set up sending limits
- [ ] Add bounce handling

---

## Security Model Tasks

- [ ] Implement JWT-based authentication
- [ ] Create short-lived stream tokens
- [ ] Ensure no direct media server exposure
- [ ] Add rate limiting on all endpoints
- [ ] Implement input sanitization
- [ ] Set up TLS/SSL configuration

---

## Infrastructure Tasks (Pre-deployment)

### Phase 0: Single-Node Setup

- [ ] Deploy PostgreSQL container
- [ ] Deploy Redis container
- [ ] Deploy FastAPI container
- [ ] Configure Nginx reverse proxy
- [ ] Set up `/mnt/media` storage volume

### Phase 1: Vertical Scaling

- [ ] Enable hardware transcoding support
- [ ] Tune PostgreSQL parameters
- [ ] Add Redis-backed metadata caching
- [ ] Optimize disk I/O (SSD)

### Phase 2: Horizontal Expansion

- [ ] Deploy media servers on dedicated nodes
- [ ] Set up database replication
- [ ] Configure load balancer
- [ ] Implement distributed storage
