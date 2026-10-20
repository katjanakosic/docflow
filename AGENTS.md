# DocFlow – instructions for coding agents

DocFlow turns supplier invoices and purchase orders (PDF) into validated,
ERP-ready data. A human reviewer approves every document. The full product
spec lives in docs/spec (link it here once exported).

## Repository layout
- web/                 Next.js (App Router, TypeScript), npm
- api/                 FastAPI (Python 3.12, uv), shared domain code
- api/app/workers/     background workers (separate process, same Python package)
- validation-service/  ASP.NET Core (.NET 10)
- evals/               labeled sample documents + eval script
- infra/               Terraform; compose.yaml stays at the repo root
- docs/                design doc, decision records

## Commands
- Infra:  docker compose up -d
- Web:    cd web && npm run dev | npm run lint | npx tsc --noEmit
- API:    cd api && uv run uvicorn app.main:app --reload | uv run pytest | uv run ruff check .

## Rules
- Small changes. Explain what you changed and why before finishing.
- Every behavior change comes with a test, including at least one failure case.
- Business logic stays out of route handlers; it lives in services behind interfaces.
- Document status changes only through the domain state machine.
- Never log document content, personal data or secrets. Never hardcode secrets.
- Money is Decimal, never float. Timestamps are UTC.
- Do not add new dependencies without saying why.
