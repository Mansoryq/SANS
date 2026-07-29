# Smart Airport Notification System (SANS) - Enterprise Edition

SANS is a production-ready, cloud-native backend application for managing airport flights, passengers, and notifications. 

## 🚀 Phase 3: Cloud Native Infrastructure

This project has been architected using modern Clean Architecture principles and is designed for zero-downtime, scalable deployment using free-tier cloud services.

### Tech Stack
- **API & Web**: FastAPI, Python 3.11
- **Database**: PostgreSQL (via Supabase)
- **Caching & Rate Limiting**: Upstash Redis
- **Storage**: Supabase Storage
- **Observability**: Sentry (Error Tracking), PostHog (Analytics)
- **Background Jobs**: APScheduler Worker Node
- **Containerization**: Docker & Docker Compose
- **Deployment**: Render (Zero-config `render.yaml`)
- **CI/CD**: GitHub Actions

### Architecture
- **API Layer**: Route definitions and request parsing.
- **Service Layer**: Core business logic, event generation, passenger synchronization.
- **Repository Layer**: Database access and ORM abstraction.
- **Queue/Worker**: Asynchronous notification dispatch with Exponential Backoff and DLQ.

## 🛠 Local Development Setup

1. Copy `.env.example` to `.env` and fill in the required values.
2. Build and start the containers:
   ```bash
   docker-compose up --build -d
   ```
3. Run database migrations:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

## 🌐 Production Deployment (Render)

SANS includes a `render.yaml` for automatic, zero-configuration deployment to Render.
Simply connect your GitHub repository to Render and it will automatically provision a Web Service and a Background Worker.

Please see the [Deployment Guide](deployment_guide.md) for full instructions on setting up Supabase, Upstash, Sentry, and PostHog.
