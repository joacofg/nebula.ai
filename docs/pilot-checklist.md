# Nebula Pilot Checklist

Use this checklist before a pilot review, academic walkthrough, or live demo. It supports the benchmark-led flow described in [demo-script.md](demo-script.md).

## Environment

- [ ] `deploy/selfhosted.env` is populated from `deploy/selfhosted.env.example`
- [ ] `NEBULA_ADMIN_API_KEY` and `NEBULA_BOOTSTRAP_API_KEY` are real values
- [ ] `docker compose -f docker-compose.selfhosted.yml up -d` succeeds
- [ ] `curl http://localhost:8000/health` returns success
- [ ] `http://localhost:3000` loads the operator console

## Benchmark artifact prep

- [ ] Run `make benchmark-demo`
- [ ] Open the newest benchmark artifact under `artifacts/benchmarks/<timestamp>/report.md`
- [ ] Confirm the benchmark artifact shows key takeaways, route and cost highlights, and fallback resilience
- [ ] Capture the exact savings sentence you plan to say out loud during the demo

## Console routes to open

- [ ] Playground is ready for one live request
- [ ] Observability is ready for usage-ledger review
- [ ] The admin key is available so the console session can be established quickly

## Degraded and fallback prep

- [ ] Pick one fallback or degraded moment to explain explicitly
- [ ] Be ready to point from the benchmark artifact to the Playground response metadata
- [ ] Be ready to point from Playground to the recorded ledger evidence for the same request
- [ ] Be ready to show Observability and explain that degraded optional dependencies do not block gateway readiness

## Trust boundary prep

- [ ] Be ready to say: Nebula is self-hosted with an optional hosted control plane
- [ ] Be ready to say: the hosted plane is not in the request-serving path and default export is metadata-only
- [ ] Be ready to say: hosted onboarding is outbound-only and starts with a short-lived enrollment token.
- [ ] Be ready to say: after enrollment, the gateway uses a deployment-scoped hosted-link credential for steady-state communication.
- [ ] Be ready to say: if the hosted plane disappears, the gateway keeps serving and hosted visibility simply becomes stale or offline.
- [ ] Be ready to say: v2.0 hosted remote management is limited to one audited rotate_deployment_credential action.
- [ ] Be ready to say: the hosted plane is metadata-and-intent only; local runtime policy and request serving remain authoritative inside the self-hosted gateway.
- [ ] Know the excluded-by-default list exactly: raw prompts, raw responses, provider credentials, raw usage-ledger rows, tenant secrets, and authoritative runtime policy state
- [ ] Do not improvise hosted powers beyond outbound-only enrollment, fleet visibility, and the audited rotate_deployment_credential action.

## Walkthrough order

- [ ] Establish the operator surface briefly
- [ ] Show the benchmark artifact first
- [ ] Run or discuss one Playground request
- [ ] Finish in Observability

## Out of scope reminders

- [ ] Do not improvise hosted powers beyond outbound-only enrollment, fleet visibility, and the audited rotate_deployment_credential action.
- [ ] Do not describe estimated premium cost as invoice-accurate billing
- [ ] Do not drift from the benchmark-led script into a long exploratory product tour
