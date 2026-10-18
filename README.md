# NetHub Payment Gateway (NetPay)

NetPay is being rebuilt as a minimal, multi-merchant M-Pesa Daraja gateway.

## Start here

- Agent rules: [AGENTS.md](AGENTS.md)
- Implementation brief for Grok/other coding agents: [docs/REBUILD_SPEC.md](docs/REBUILD_SPEC.md)

## Product scope

Core: merchant-owned Daraja integrations, STK Push, hosted STK callbacks, transaction verification where supported, reconciliation, M2M access and reliable payment events.

Conditional: C2B validation/confirmation and Daraja C2B URL registration. C2B URLs are generated and stored for each integration, but registration is opt-in. STK-only merchants must not be forced to register C2B URLs.

Frontend: Next.js App Router and TypeScript, with SEO-friendly public pages and a private merchant dashboard.

## Repository and deployment

Git history is preserved. The rebuild is developed on `work/minimal-netpay-rebuild`, created from `main`. The existing GitHub Actions workflows, GHCR image identity, Docker/deployment configuration and release intent must be retained and adapted to the new implementation.

Do not merge the rebuild into `main` until the acceptance criteria in the implementation brief pass.