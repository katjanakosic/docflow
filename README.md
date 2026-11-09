# DocFlow

DocFlow turns supplier invoices and purchase orders that arrive as PDFs into validated, structured data, with a human approving every record. An LLM reads each document in the background; a reviewer checks the result side by side with the original PDF and approves or rejects it.

It's built for a (fictional) Swiss wholesaler whose accounts-payable team receives documents in German, French, Italian and English, and currently retypes them by hand.

![DocFlow document page: the original PDF next to the extracted data](docs/screenshot.png)

## Features

- **Upload PDFs** with duplicate detection by SHA-256 fingerprint
- **Background extraction** with Claude: a Redis job queue and a separate worker process, so uploads return immediately
- **Retries with exponential backoff** for temporary failures, plus a manual retry for documents that still fail
- **Structured output you can trust:** forced tool use with a JSON schema generated from Pydantic models, and every answer validated before it's saved
- **Review screen** with the original PDF next to the extracted data, low-confidence fields highlighted, and approve or reject with a reason
- **Live status updates** in the browser while documents are processed
- **A state machine** that guards every status change, so a document can't skip or repeat a step
- **Measured extraction quality:** an eval script scores the extractor against 20 labeled sample documents in four languages

## Architecture

```mermaid
flowchart LR
    Browser["Browser<br/>(Next.js)"] -->|"/api/* proxied"| API["FastAPI API"]
    API --> PG[("PostgreSQL<br/>records")]
    API --> S3[("MinIO / S3<br/>PDF files")]
    API -->|enqueue job| Redis[("Redis<br/>job queue")]
    Worker["RQ worker"] -->|take job| Redis
    Worker --> PG
    Worker --> S3
    Worker -->|"PDF + schema"| Claude["Claude API"]
    Browser -.->|"presigned link (5 min)"| S3
```

- **The API** stores each upload in object storage, writes a record to Postgres, and queues an extraction job. It never waits for the LLM.
- **The worker** takes jobs from the queue, sends the PDF to Claude, validates the answer and saves it.
- **The browser** loads PDFs directly from storage through short-lived presigned links, so files never pass through the API.

Inside the API, the code follows a **ports-and-adapters** structure: business logic in `domain/` and `services/` depends only on interfaces (`Storage`, `DocumentRepository`, `Extractor`, `ExtractionQueue`). Each interface has a real implementation (S3, Postgres, Claude, Redis) and a lightweight one for tests, wired together through FastAPI's dependency injection. Swapping MinIO for S3, or the in-memory repository for Postgres, was a one-line change in `deps.py`.

### Document lifecycle

```mermaid
stateDiagram-v2
    [*] --> uploaded
    uploaded --> extracting: worker starts
    extracting --> needs_review: data extracted
    extracting --> extraction_failed: 3 attempts failed
    extraction_failed --> uploaded: retry
    needs_review --> approved: approve
    needs_review --> rejected: reject
    approved --> exported: export (planned)
    approved --> export_failed: export failed (planned)
    export_failed --> approved: retry (planned)
```

Every transition goes through one pure function, `transition(status, action)`, tested against all 64 status-and-action combinations.

## Extraction quality

The eval script (`api/scripts/run_eval.py`) runs all 20 sample documents through the real extractor and compares 11 fields per document with hand-made labels.

| Prompt | Model | Field accuracy | What changed |
| --- | --- | --- | --- |
| v1 | Claude Haiku | 92.3% | Baseline. The VAT number lost its `MWST`/`TVA`/`IVA` suffix on 17 of 20 documents. |
| v2 | Claude Haiku | 99.5% | Added one rule with an example for VAT numbers. One remaining error: an Italian date `11/06/2026` read as November 6 instead of June 11. |

The remaining error is the kind a human reviewer and business validation are there to catch, which is why DocFlow never exports without approval.

## Tech stack

| Area | Technologies |
| --- | --- |
| Frontend | Next.js (App Router, Cache Components), React, TypeScript, TanStack Query, Tailwind CSS |
| API | Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Background jobs | Redis, RQ |
| Storage | PostgreSQL (with JSONB for extracted data), MinIO (S3-compatible) |
| AI | Anthropic Claude API: PDF input, forced tool use, structured output |
| Tooling | uv, ruff, pytest, Docker, Docker Compose, GitHub Actions |

## Getting started

### Prerequisites

- [Docker](https://www.docker.com/) with Docker Compose
- [Node.js](https://nodejs.org/) 22 or later, with npm
- [uv](https://docs.astral.sh/uv/) for Python
- An [Anthropic API key](https://platform.claude.com) for extraction

### 1. Configure

```bash
git clone https://github.com/katjanakosic/docflow.git
cd docflow
cp .env.example .env
```

Open `.env` and set `ANTHROPIC_API_KEY`. The other values work as they are for local development.

### 2. Start the backend

```bash
docker compose up -d --build
```

This starts Postgres, Redis, MinIO, the API and the worker. The API applies database migrations when it starts.

Then create the storage bucket once: open the MinIO console at http://localhost:9001, log in with the credentials from `.env`, and create a bucket named `docflow-documents`.

### 3. Start the frontend

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000 and upload one of the sample PDFs from `evals/samples/`. The API's interactive documentation is at http://localhost:8000/docs.

### Developing the backend locally

While working on API code, run it on your machine instead of in Docker, so it reloads on every save:

```bash
docker compose stop api worker
cd api
uv run uvicorn app.main:app --reload
```

and in a second terminal, also inside `api/`:

```bash
uv run rq worker extraction --url redis://localhost:6379/0 --worker-class rq.SimpleWorker
```

## Tests

```bash
cd api
uv run pytest
```

The storage and repository tests run twice: once against the in-memory implementations, and once against MinIO and a Postgres test database. Without those running, the second set is skipped. To enable the Postgres tests, create and migrate the test database once:

```bash
docker compose exec postgres createdb -U docflow docflow_test
cd api
DATABASE_URL=postgresql+psycopg://docflow:docflow@localhost:5432/docflow_test uv run alembic upgrade head
```

Frontend checks, inside `web/`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```

CI runs linting, type checks, the build and all tests on every push.

## Evals

```bash
cd evals
uv run python generate_samples.py      # regenerate the 20 labeled sample PDFs

cd ../api
uv run --env-file ../.env python -m scripts.run_eval
```

Results are written to `evals/results/`, one file per prompt version and model, so runs can be compared.

## Project structure

```text
docflow/
├── api/                      FastAPI app and worker (one Python package)
│   ├── app/
│   │   ├── api/              HTTP endpoints and dependency providers
│   │   ├── services/         use cases: upload, extraction, review, retry
│   │   ├── domain/           models, state machine, interfaces
│   │   ├── adapters/         S3, Postgres, Claude, Redis, and test implementations
│   │   └── workers/          background job functions
│   ├── migrations/           Alembic database migrations
│   ├── scripts/              eval runner
│   └── tests/
├── web/                      Next.js frontend
├── evals/                    sample generator, labeled PDFs, eval results
└── compose.yaml              local infrastructure, API and worker
```

## Design decisions

- **A human approves every document.** It's financial data; the AI proposes, a person decides.
- **Extraction runs in a worker, not in the request.** LLM calls are slow and can fail; uploads shouldn't wait, and failures should be retried.
- **Files in object storage, records in Postgres.** Large files don't belong in the database; searchable, transactional records don't belong in object storage.
- **Extracted data in a JSONB column** instead of separate tables for line items: one row per document, still queryable, and much simpler.
- **Interfaces at every external boundary.** Tests run in milliseconds without Docker or an API key, and implementations can be swapped through configuration.
- **Migrations run when the API container starts.** Simple and safe for a single instance; with several instances, they'd become a separate deployment step.

## Future work

- **Login and roles**, including the four-eyes rule: nobody may approve a document they uploaded
- **A .NET validation and export service** checking business rules (totals, Swiss VAT rates) and producing ERP-ready exports
- **Deployment to AWS:** ECS Fargate for the API and worker, RDS, ElastiCache or SQS, S3, behind a load balancer
- **The frontend as a Compose service**, plus end-to-end browser tests
- **Pagination** for the document list and an append-only **audit log**