# NetHub Payment Gateway (NetPay)

NetPay is being rebuilt as a minimal, multi-merchant M-Pesa Daraja gateway.

## Start here

- Agent rules: [AGENTS.md](AGENTS.md)
- Implementation brief: [docs/REBUILD_SPEC.md](docs/REBUILD_SPEC.md)
- Verified Daraja capability notes: [docs/DARAJA_CAPABILITIES.md](docs/DARAJA_CAPABILITIES.md)
- Backend setup and M2M bootstrap: [backend/README.md](backend/README.md)
- Deployment and migration runbook: [deploy/README.md](deploy/README.md)

## Implemented foundation

- OAuth client-credentials token exchange for merchant M2M clients, hashed client secrets, short-lived scoped bearer tokens, and merchant-level authorization.
- Encrypted Daraja integration credentials and NetPay-hosted STK callback URLs.
- STK Push initiation with KES amount validation, idempotency, explicit unknown outcomes, callback correlation, deduplication, and guarded state transitions.
- Opt-in C2B URL registration and confirmation handling; external validation currently checks basic shape/shortcode/amount only, not merchant-specific account-reference rules.
- PostgreSQL-backed event outbox, signed optional merchant webhook delivery, retries/dead-letter state, and worker recovery for callbacks that race ahead of STK correlation persistence.
- Next.js App Router static public landing page and a no-index dashboard placeholder.

## Deliberate limitations

- An OAuth token proves consumer key/secret authentication, not that a shortcode/passkey has all required permissions.
- STK initiation acceptance is not proof of payment.
- Daraja Transaction Status requires additional initiator/authorization configuration. NetPay must not claim provider verification until the relevant product and credentials are confirmed for a merchant.
- C2B registration is optional. Do not enable production external validation when merchant-specific account validation rules are required; that policy is not implemented yet.
- The dashboard does not yet include NetHub identity/session integration and must not expose merchant data until that is completed.
- A frontend package lockfile still needs to be generated and committed; CI currently installs the pinned direct dependency versions with npm install.

## Repository and deployment

The frontend npm lockfile is committed and CI uses `npm ci`. A backend `uv.lock` is still outstanding; the current backend install resolves the declared version ranges, so pin and commit the Python lock before treating builds as fully reproducible.

Git history is preserved. The rebuild is developed on `work/minimal-netpay-rebuild`, created from `main`. The existing GHCR image identity and release intent are retained and the Docker/Kubernetes/Compose files are being adapted to the new API and static frontend.

Do not merge the rebuild into `main` until migrations, backend tests, frontend lint/typecheck/build, container build, and the acceptance criteria in the implementation brief pass.
