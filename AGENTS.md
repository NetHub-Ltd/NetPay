# NetPay Agent Instructions

Read [the minimal rebuild implementation brief](docs/REBUILD_SPEC.md) before changing code.

## Non-negotiable constraints
- Work on `work/minimal-netpay-rebuild`; do not modify `main` or create additional branches.
- Preserve Git history and the existing CI, GHCR release/image publishing and deployment contract. Adapt workflow paths only as required by the new architecture; do not delete these workflows.
- Build NetPay as a multi-merchant Daraja gateway. Each merchant supplies its own shortcode and credentials.
- STK Push is core. Generate and persist NetPay-hosted STK callback URLs automatically.
- C2B URL generation is automatic, but C2B registration is optional and only occurs when explicitly enabled. STK-only merchants must not be forced to register C2B URLs.
- PostgreSQL is the financial source of truth. Redis is auxiliary; all important reconciliation and event work must be recoverable from PostgreSQL.
- No Cloudflare Worker, Celery, Kafka, separate broker, microservices or unrelated payment products in the initial release.
- Use FastAPI, SQLModel, PostgreSQL/asyncpg, Alembic, pytest and Loguru for the backend; Next.js App Router and strict TypeScript for the frontend.
- Never log or return secrets. Never infer payment success from STK initiation acceptance. Treat callbacks as untrusted and idempotent.
- Verify uncertain Daraja behavior against official docs/sandbox rather than guessing.
- Run relevant tests and report exact commands/results. Do not claim tests passed unless they were run.
- Keep changes reviewable; do not merge the branch until all acceptance criteria in the implementation brief are met.

## First task
Before editing application code, inventory the current repository and deployment contract. Summarize what must be retained, replaced and adapted. Then propose the schema, payment state machine, API contracts and Daraja capability matrix for review. Do not immediately delete files or start a broad rewrite.
