# NetPay engineering instructions

Read this file, docs/REBUILD_SPEC.md, the active issue/implementation contract and the relevant skills before changing application code. Refresh the NetHub-Ltd/skills- repository before substantial engineering work and apply the current CORE and FRONTEND standards; use HUMAN-EXPERIENCE and VISUAL-DESIGN for user-facing work.

## Repository workflow

- Work on a focused topic branch created from the latest verified dev branch.
- Open pull requests targeting dev. The repository owner performs the final merge.
- Never push directly to dev or main. Do not rebase, squash, reset, force-push or merge on the owner's behalf.
- Do not publish a release, apply production infrastructure or alter live secrets without explicit authorization.
- Verify the exact base commit and record it in the PR. A source archive is useful context but does not establish branch identity.
- Inspect the complete relevant source, deployment, CI and test paths before implementation. Do not infer that a partial file fetch represents the full repository.

## Current application architecture

- Next.js App Router is an independently deployed Node.js server using standalone output.
- Next.js owns public rendering, login/callback, application sessions and the same-origin HTTP BFF.
- Browser-originated NetPay HTTP API calls must go through the Next.js BFF. Browser JavaScript must never receive IdP access/refresh tokens or call FastAPI directly.
- FastAPI is an independently deployed API service. It owns payment/domain rules, M2M contracts, merchant membership, tenant isolation, persistence, provider callbacks and business authorization.
- The BFF's opaque session handle is stored as a hash; upstream tokens are encrypted at rest in PostgreSQL using a dedicated key. Internal session-store routes are service-to-service only and must not be exposed by public ingress.
- Zitadel authenticates users; NetHubKe remains the identity/access resource server. NetPay must not become an IdP or password store.
- M2M clients and Safaricom callbacks retain their existing API contracts.
- No static export or FastAPI static frontend hosting. Do not add a WebSocket gateway/broker without a concrete realtime product requirement; design ingress routing and authentication deliberately when one is needed.

## Non-negotiable engineering constraints

- Build NetPay as a multi-merchant Daraja gateway. Each merchant supplies their own shortcode and credentials.
- STK Push is core. Generate and persist NetPay-hosted STK callback URLs automatically.
- C2B registration is opt-in. STK-only merchants must not be forced to register C2B URLs.
- PostgreSQL is the financial source of truth. Redis is auxiliary; important reconciliation and event work must be recoverable from PostgreSQL.
- Do not introduce Cloudflare Workers, Celery, Kafka, another broker or unrelated microservices without an approved concrete need.
- Use FastAPI, SQLModel, PostgreSQL/asyncpg, Alembic, pytest and Loguru for the backend; Next.js App Router and strict TypeScript for the frontend. Avoid TypeScript any.
- Never log or return secrets. Never infer payment success from STK initiation acceptance. Treat callbacks as untrusted and idempotent.
- Preserve merchant/tenant authorization in FastAPI. Frontend visibility is never an authorization boundary.
- Verify uncertain Daraja behavior against official docs/sandbox rather than guessing.

## Quality and delivery

- Add meaningful positive and negative tests for behavior and security boundaries.
- Run relevant backend tests, frontend lint/typecheck/build, container builds and deployment validation. Report exact commands and results; never claim tests passed unless actually run.
- Keep changes reviewable and scoped to the approved issue. Update affected docs, trackers, environment examples and CI in the same delivery.
- Preserve GHCR API image identity and release behavior; publish the separate frontend image alongside it.
- Keep production secrets out of git, PR comments and chat.
- Do not claim live staging acceptance before the owner's merge and the resulting deployment have been verified.
