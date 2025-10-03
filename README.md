# Summarizer API

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)

Async **FastAPI** service + **ARQ worker** that fetches a web page and summarizes it using **Ollama** (model: `gemma3:1b`).  
Persistence via **Postgres**, background jobs via **Redis**.

---

## Table of Contents

- [Summarizer API](#summarizer-api)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Project Layout](#project-layout)
  - [Quickstart (Docker)](#quickstart-docker)
  - [Local Dev (w/o Docker)](#local-dev-wo-docker)
  - [API Docs \& OpenAPI](#api-docs--openapi)
  - [cURL examples](#curl-examples)
  - [Testing](#testing)
  - [Common Tasks](#common-tasks)

---

## Features

- **FastAPI** (async, DI, repository pattern)  
- **ARQ worker** for background summarization  
- **Postgres** storage (SQLAlchemy 2.x async)  
- **Redis** queue  
- **Ollama** (local LLM) with `gemma3:1b`  
- **pytest** tests (unit tests use in-memory fakes; can run against Postgres too)  
- **mypy** (strict) & **ruff** for quality  
- **Docker Compose** stack (db, redis, api, worker, ollama, webui)  
- **OpenAPI** schema + Swagger UI  

---

## Requirements

Install these on your system:

- **Python 3.12**  
- **uv** (Python package manager): [uv](https://github.com/astral-sh/uv)  
- **Docker & Docker Compose**  
- **Task** (Taskfile runner):  
  ```bash
    go install github.com/go-task/task/v3/cmd/task@latest
  ```
Optional (usually installed via uv run ... anyway):
ruff, mypy, pytest, pytest-cov, pytest-asyncio.

## Project Layout
```bash
    alembic/                # Alembic migrations
    api-doc/                # OpenAPI json
    deploy/                 # docker-compose + Dockerfiles
    src/
      app/
        api/
          main.py           # FastAPI app
          routers/          # /documents endpoints
          domain/           # repositories (DB access)
        core/               # models, schemas, middleware etc.
        worker/             # ARQ worker (tasks, utils)
    tests/                  # pytest tests (units use in-memory fakes)
    Taskfile.yml            # dev automation
    pyproject.toml          # deps and tooling
```
## Quickstart (Docker)

Bring everything up:
```bash
  task docker:up
```

What happens under the hood:
- Pulls image tags + ensures Ollama image + pulls model
- Starts db, redis, api, worker, ollama, webui
- Runs alembic upgrade head inside the API container

Tear down:

```bash
  task docker:down
```

Check logs:
```bash
docker compose -f deploy/docker-compose.yml logs -f
# per service: logs -f api | worker | db | redis | ollama
```
## Local Dev (w/o Docker)

Run API:
```bash
  task run:api
```

Run worker:

```bash
  task run:worker
```

For local dev without Docker, ensure a Postgres and Redis are reachable and you’ve set DATABASE_URL, REDIS_HOST, REDIS_PORT, and OLLAMA_API (defaults point to the compose services).

## API Docs & OpenAPI

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: GET /documents/health

Export OpenAPI (JSON):

```bash
  task docs:openapi
```

## cURL examples

```bash
  curl -X POST http://localhost:8000/documents/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Article Summaries","url":"https://www.trentu.ca/academicskills/how-guides/how-write-university/how-approach-any-assignment/writing-article-summaries"}'

  curl http://localhost:8000/documents/{UUID}/
  curl "http://localhost:8000/documents/?limit=50&offset=0"
```

## Testing

Unit tests (default)

- Use in-memory fakes for repositories (no DB or Testcontainers).
- External calls (fetch_and_extract, call_ollama) are mocked.

Run:
  ```bash
  task test
  ```
With coverage
```bash
  task test:coverage
```

## Common Tasks
```bash
  task lint          # ruff
  task typecheck     # mypy (strict)
  task docker:pull   # pulls api + worker images
  task docker:up     # bring up full stack
  task docker:down   # stop & remove containers + volumes
  task docs:openapi  # export OpenAPI JSON
```

## Architecture Decisions

### Why this design?
- **Separation of concerns**:  
  - **API** -> handles fast requests (create, list, get documents).  
  - **Worker** -> runs slow/background jobs (fetch, extract, summarize).  
  This keeps the API responsive even if summarization is slow or fails.

- **Scalability**:  
  - API and Worker are separate containers -> each can scale independently.  
  - Add more API replicas for traffic, or more Worker replicas for throughput.  
  - Redis queue absorbs bursts and balances jobs across workers.

- **Robustness**:  
  - Failures in the Worker do not affect API uptime.  
  - Jobs are idempotent and retryable (document re-fetched by UUID).  
  - Clear statuses (`PENDING -> PROCESSING -> SUCCESS/FAILED`) for monitoring and recovery.  
  - Timeouts on all external calls (web fetch, Ollama).

- **Repository pattern**:  
  - Business rules (e.g. uniqueness, re-summarization) live in the repository, keeping the router thin.  
  - Easier testing (can mock repository in unit tests).

- **Containers & deployability**:  
  - API, Worker, Redis, Postgres, and Ollama run as separate services.  
  - Alembic migrations ensure DB schema is up to date.  
  - Docker images published for reproducible deployments.

### Key Benefits
- **Scalable**: horizontally scale API and Worker separately.  
- **Robust**: resilient to failures and retries, API remains healthy under load.  
- **Maintainable**: clean boundaries (API vs Worker, router vs repo).  
- **Observable**: structured logging at all critical steps.

> **In short:** Fast API calls are decoupled from heavy summarization work via an async worker + queue. This design ensures responsiveness, fault isolation, and easy horizontal scaling.
