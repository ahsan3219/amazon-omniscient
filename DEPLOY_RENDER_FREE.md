# Render Free deployment notes

## Scope and important limitations

This blueprint deploys the FastAPI API and Next.js UI as two Free web services. It does not provision PostgreSQL or Redis: use external free-tier providers and set their connection URLs in the Render dashboard. Do not use Render Free Postgres for durable data; it expires after 30 days. Render Free Key Value has only 25 MB and no persistence.

Render Free does not provide free Background Worker services. The application currently dispatches analysis, scraping, tracking and scheduled maintenance through Celery queues. Therefore this blueprint alone deploys the UI/API but does NOT execute those queued tasks. The full workflow needs a worker runtime. Do not point production users at this deployment until a worker execution strategy is connected and tested.

A Render Free web service has 512 MB RAM and 0.1 CPU, sleeps after 15 minutes without inbound traffic, loses local filesystem changes on restart/sleep/redeploy, and shares a 750 free-instance-hour monthly workspace allowance. A periodic HTTP ping may reduce idle sleep, but cannot prevent platform restarts, guarantee availability, or create more monthly hours. Chromium scraping and Next.js + API + Celery in one 512 MB process is not a realistic configuration.

## Configure external data stores

Create an external PostgreSQL database and Redis-compatible service on free tiers that meet your data retention and connection requirements. Use the provider's async PostgreSQL URL for DATABASE_URL, with SQLAlchemy's asyncpg driver form:

`postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME?ssl=require`

Set REDIS_URL, CELERY_BROKER_URL and CELERY_RESULT_BACKEND to the Redis-compatible provider URLs. If the provider supplies a TLS URL, preserve its TLS scheme/options and verify the redis-py/Celery TLS configuration.

## Render API environment

- DATABASE_URL: external PostgreSQL asyncpg URL
- REDIS_URL: Redis URL
- CELERY_BROKER_URL: Redis URL (e.g. database 1 if provider supports Redis DB indexes)
- CELERY_RESULT_BACKEND: Redis URL (e.g. database 2 if supported)
- GEMINI_API_KEY: Google AI Studio key
- LLM_PROVIDER: gemini
- LLM_MODEL: gemini-2.5-flash
- APP_SECRET_KEY: strong random secret (blueprint generates one)
- ALLOWED_ORIGINS: exact frontend origin, e.g. https://omniscient-frontend.onrender.com

## Render frontend environment

- NEXT_PUBLIC_API_URL: https://YOUR-API.onrender.com
- INTERNAL_API_URL: https://YOUR-API.onrender.com

NEXT_PUBLIC_API_URL is embedded into the browser bundle at build time. Set it before the first frontend build and redeploy after changing it.

## Worker requirement

The repository's Celery app defines analysis, scraping, tracking and beat schedules. A separate process must run:

```bash
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1 -Q default,analysis,tracking,scraping
celery -A app.workers.celery_app beat --loglevel=info --pidfile=/tmp/celerybeat.pid
```

Those are separate processes and must not be started as two Render web services on Free if you intend to keep them always-on: they consume workspace free hours and still have no reliable always-on guarantee. Render Background Workers and Cron Jobs are not available on Free plans. For zero-cost experiments, use a separate on-demand worker runner (for example a GitHub Actions workflow dispatched when jobs are queued) and accept queue latency and runtime limits; this requires implementing and securing a queue-dispatch bridge before it is production-ready.

## First deploy

1. Create the external PostgreSQL and Redis-compatible services.
2. In Render, create a Blueprint from this repository and select branch `feat/gemini-render-free`.
3. Fill the external database/Redis URLs and Gemini API key when prompted.
4. After the API deploys, copy its `onrender.com` URL into both frontend URL environment variables.
5. Set the API ALLOWED_ORIGINS to the frontend `onrender.com` origin and redeploy the API.
6. Verify `/health`, open the frontend, save Gemini settings and test a small AI request.
7. Before running analysis, implement and verify the worker runner. Do not assume a green API health check means Celery tasks are being processed.

## Security before public launch

The current settings API uses a single hard-coded `default` user and the API routes are not protected by a complete authentication layer. Do not expose a public instance with real Amazon credentials or API keys until authentication/authorization and proper credential encryption are implemented. The current settings route stores some credentials as raw bytes; bytes are not encryption.
