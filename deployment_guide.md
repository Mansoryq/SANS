# SANS Enterprise Deployment Guide

This guide explains how to deploy the SANS application using fully managed free-tier cloud services.

## Prerequisites
1. A GitHub account with your repository hosted.
2. Accounts for:
   - [Render](https://render.com) (Compute)
   - [Supabase](https://supabase.com) (PostgreSQL & Storage)
   - [Upstash](https://upstash.com) (Redis)
   - [Sentry](https://sentry.io) (Error Tracking)
   - [PostHog](https://posthog.com) (Analytics)

---

## 1. Supabase Setup (Database & Storage)
1. Log in to Supabase and create a new project.
2. Go to **Settings > Database** and copy the **Connection string (URI)**.
   - Replace `[YOUR-PASSWORD]` with your actual password.
   - Example: `postgresql://postgres.[ref]:[password]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`
3. Go to **Settings > API** and copy the `URL` and `anon` public key for Supabase Storage.
4. *Optional*: Create a new bucket in Storage named `sans_assets` and make it public.

## 2. Upstash Setup (Redis)
1. Log in to Upstash and create a new Redis database.
2. Select the region closest to your application deployment (e.g., Frankfurt).
3. Scroll down and copy the **Endpoint** and **Password** to construct the `REDIS_URL`.
   - Format: `rediss://default:[password]@[endpoint]:[port]`

## 3. Observability (Sentry & PostHog)
**Sentry:**
1. Create a Sentry project (FastAPI / Python).
2. Copy the `DSN` URL provided during onboarding.

**PostHog:**
1. Create a PostHog project.
2. Copy the **Project API Key** and **Host** (e.g., `https://eu.i.posthog.com`).

---

## 4. Render Deployment

We use a declarative `render.yaml` file (Infrastructure as Code) which automatically provisions a **Web Service** and a **Background Worker**.

1. Go to your Render Dashboard.
2. Click **New > Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect the `render.yaml` file.
5. You will be prompted to enter the required Environment Variables.
   - `DATABASE_URL`: Your Supabase connection string.
   - `REDIS_URL`: Your Upstash connection string.
   - `SENTRY_DSN`: Your Sentry DSN.
   - `POSTHOG_API_KEY`: Your PostHog API key.
   - `SUPABASE_URL` and `SUPABASE_KEY`: Your Supabase API credentials.
6. Click **Apply**.
7. Render will build the Docker container and start both the `web` and `worker` services.

## 5. Post-Deployment (Migrations)

Since Render's free tier spins down, running migrations dynamically on startup can cause timeouts. It's recommended to run migrations via GitHub Actions or locally pointing to your production DB:

```bash
export DATABASE_URL="postgresql://[user]:[password]@[host]:6543/postgres"
alembic upgrade head
```

## Scaling Recommendations
- **Database Connection Limits**: The Supabase free tier connection limit is handled by Supabase's built-in PgBouncer (pooler URL on port `6543`).
- **Render Spin-Down**: The free Web service spins down after 15 minutes of inactivity. For real commercial use, upgrade to the Render Starter plan ($7/mo) to prevent spin-down and ensure background workers process queues 24/7.
- **Cache Sizing**: Upstash free tier allows 10k requests/day. Adjust the polling interval in SANS settings if you exceed this limit.
