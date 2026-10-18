# NetPay Agent Instructions

Read [the minimal rebuild implementation brief](docs/REBUILD_SPEC.md) before changing code.

## Non-negotiable constraints
- Work only on `work/minimal-netpay-rebuild`; do not modify `main` or create additional branches.
- Preserve Git history and the existing CI, GHCR release/image publishing and deployment contract. Adapt workflow paths to the new architecture; do not delete these workflows.
- The legacy application source has intentionally been pruned from this branch. Do not restore it. Rebuild against the specification.
- Build NetPay as a multi-merchant Daraja gateway. Each merchant supplies their own shortcode and credentials.
- STK Push is core. Generate and persist NetPay-hosted STK callback URLs automatically.
- C2B URL generation is automatic, but C2B registration is optional and only occurs when explicitly enabled. STK-only merchants must not be forced to register C2B URLs.
- PostgreSQL is the financial source of truth. Redis is auxiliary; important reconciliation and event work must be recoverable from PostgreSQL.
- No Cloudflare Worker, Celery, Kafka, separate broker, microservices or unrelated payment products in the initial release.
- Use FastAPI, SQLModel, PostgreSQL/asyncpg, Alembic, pytest and Loguru for the backend; Next.js App Router and strict TypeScript for the frontend.
- Never log or return secrets. Never infer payment success from STK initiation acceptance. Treat callbacks as untrusted and idempotent.
- Verify uncertain Daraja behavior against official docs/sandbox rather than guessing.
- Run relevant tests and report exact commands/results. Do not claim tests passed unless they were run.
- Keep changes reviewable; do not merge until all acceptance criteria in the implementation brief are met.

## First task
Before implementing application code, inventory the retained GitHub Actions, Dockerfile, compose/Kubernetes manifests, environment examples, release/image publishing behavior, and runtime expectations. Summarize what must be retained, replaced and adapted. Then propose the schema, payment state machine, API contracts and Daraja capability matrix. Do not start a broad implementation until that design is documented. After the design is reviewed, implement the specified vertical slices and update CI/deployment files together with the new app so the final branch is buildable and deployable.
