# Getting Started

This guide walks you through running **RLM Data Agent** locally — backend, frontend, background workers, and LLM configuration.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.13+ | Managed via [uv](https://docs.astral.sh/uv/) |
| Node.js | 20+ | For the frontend |
| PostgreSQL | 15+ | Metadata, users, chat history |
| Redis | 8+ | Celery task broker |
| LLM server | any | OpenAI-compatible API (LM Studio, vLLM, OpenAI, etc.) |

---

## 1. Clone and configure

```bash
git clone <your-repo-url>
cd "RLM Agent"
```

### Backend environment

Create `backend/.env` with at minimum:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rlm_agent

# Security
JWT_SECRET_KEY=change-me-to-a-long-random-string

# LLM (OpenAI-compatible)
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=your-model-name

# Optional
DEBUG=true
STORAGE_PATH=storage
MAX_UPLOAD_SIZE_MB=500
CORS_ORIGINS=["http://localhost:5173"]
REDIS_URL=redis://localhost:6379/0
```

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `JWT_SECRET_KEY` | Secret for signing JWT access tokens |
| `LLM_BASE_URL` | Base URL of your OpenAI-compatible API |
| `LLM_API_KEY` | API key (use any value for local LM Studio) |
| `LLM_MODEL` | Model identifier your provider expects |
| `REDIS_URL` | Celery broker URL |
| `STORAGE_PATH` | Directory for uploaded dataset files |

---

## 2. Start infrastructure

### PostgreSQL

Create the database:

```sql
CREATE DATABASE rlm_agent;
```

### Redis

Using Docker Compose (included in the repo):

```bash
cd backend
docker compose up -d
```

This starts Redis on port `6379`.

---

## 3. Backend setup

```bash
cd backend

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start Celery worker (separate terminal)
uv run celery -A backend.workers.celery_app worker --loglevel=info

# Start the API server
uv run backend
```

The API will be available at:

- **API:** http://localhost:8000
- **Swagger docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 4. Frontend setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:5173.

The Vite dev server proxies `/api` requests to `http://localhost:8000`, so no extra CORS configuration is needed during development.

---

## 5. Configure your LLM

RLM Data Agent works with any **OpenAI-compatible** chat completions API.

### LM Studio (local)

1. Download and open [LM Studio](https://lmstudio.ai/)
2. Load a model (instruction-tuned models work best)
3. Start the local server on port `1234`
4. Set in `backend/.env`:

```env
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=<model-id-shown-in-lm-studio>
```

### OpenAI

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o
```

### Tips for best results

- Use models that follow structured output (`<code>` / `<final>` tags)
- Larger context windows help for datasets with many columns
- The agent may take several iterations — expect 30–120 seconds per question on local models

---

## 6. First run walkthrough

1. Open http://localhost:5173
2. **Register** a new account (or log in)
3. On the dashboard, **drag and drop** a CSV or XLSX file
4. Wait for ingestion to complete (status badge turns **Ready**)
5. Open the dataset page and **ask a question** in the chat panel, for example:
   - "How many rows are in this dataset?"
   - "What are the top 5 values in the category column?"
   - "Are there any outliers in the price column?"
6. Watch the **step timeline** as the agent writes code, runs tools, and builds its answer

---

## 7. Running tests

```bash
cd backend

# Data runtime smoke test
uv run python src/scripts/test_runtime.py

# RLM agent integration test (requires LLM)
uv run python src/scripts/test_rlm.py
```

---

## 8. Production considerations

These are not required for local development but matter for deployment:

| Concern | Recommendation |
|---------|---------------|
| `DEBUG` | Set to `false` |
| `JWT_SECRET_KEY` | Use a cryptographically random 256-bit secret |
| HTTPS | Terminate TLS at a reverse proxy (nginx, Caddy) |
| File storage | Move to S3/GCS for multi-instance deployments |
| Celery | Run multiple workers; use a dedicated Redis instance |
| Database | Connection pooling via PgBouncer for high concurrency |
| LLM | Use a hosted provider with rate limiting and monitoring |

---

## Troubleshooting

### Dataset stuck in "processing"

- Check that the Celery worker is running
- Check Redis is reachable at `REDIS_URL`
- Inspect worker logs for encoding or parsing errors

### Agent returns 500 — "LLM model is not configured"

- Ensure `LLM_MODEL` is set in `backend/.env`
- Restart the backend after changing env vars

### Agent times out or gives poor answers

- Verify your LLM server is running and reachable at `LLM_BASE_URL`
- Try a more capable model
- Check backend logs for REPL execution errors

### CORS errors in the browser

- Confirm `CORS_ORIGINS` includes your frontend URL
- In dev, use the Vite proxy (`npm run dev`) instead of calling `:8000` directly

---

## Next steps

- Read [Architecture](ARCHITECTURE.md) for a deep dive into the RLM loop and module boundaries
- Explore the API at http://localhost:8000/docs
- Review agent prompts in `backend/src/backend/rlm/prompts.py`
