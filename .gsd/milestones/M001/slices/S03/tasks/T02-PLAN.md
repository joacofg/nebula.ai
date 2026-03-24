---
estimated_steps: 5
estimated_files: 4
skills_used:
  - best-practices
---

# T02: Publish and wire the canonical migration guide

**Slice:** S03 — Reference migration integration
**Milestone:** M001

## Description

Turn the new executable proof into one canonical adoption artifact for humans: a migration guide that starts from the already-established quickstart assumptions, shows the smallest honest before/after diff for a realistic chat-completions caller, and tells adopters exactly how to confirm success through Nebula's public headers and operator evidence. Keep the S01/S02 composition rules intact by linking back to the canonical contract and production-model docs instead of restating them.

## Steps

1. Write `docs/reference-migration.md` as the single canonical migration guide for S03, using the verified proof path from `tests/test_reference_migration.py` as the source of truth.
2. Show a believable before/after integration diff for a common OpenAI-style chat-completions caller where the primary changes are base URL, `X-Nebula-API-Key`, and optional `X-Nebula-Tenant-ID`.
3. Explicitly point readers back to `docs/quickstart.md` for environment/setup, `docs/adoption-api-contract.md` for the supported public contract, and `docs/production-model.md` for tenant/operator/app/workload framing.
4. Explain the operator-evidence confirmation path using `X-Nebula-*` headers and `GET /v1/admin/usage/ledger` without implying Playground is the migration target.
5. Update `README.md` and any necessary canonical doc entry points so the migration guide is discoverable but not duplicated.

## Must-Haves

- [ ] `docs/reference-migration.md` is the single canonical human-facing migration proof for S03.
- [ ] The guide stays aligned with the tested proof path and does not reopen or duplicate the S01 contract or S02 operating-model canonicals.
- [ ] Repo entry links make the migration guide discoverable from the main adoption flow.

## Verification

- `test -f docs/reference-migration.md && rg -n "reference migration|before|after|X-Nebula-API-Key|X-Nebula-Tenant-ID|usage ledger|adoption-api-contract|quickstart|production-model" docs/reference-migration.md README.md docs/quickstart.md`
- `python3 - <<'PY'
from pathlib import Path
for path in [Path('docs/reference-migration.md'), Path('README.md')]:
    text = path.read_text()
    assert 'TODO' not in text and 'TBD' not in text
print('ok')
PY`

## Inputs

- `tests/test_reference_migration.py` — executable proof source for the migration guide
- `docs/quickstart.md` — canonical setup flow the guide must reuse instead of repeating
- `docs/adoption-api-contract.md` — canonical public compatibility boundary to reference
- `docs/production-model.md` — canonical runtime-boundary language for tenant/operator/app/workload framing
- `README.md` — repo entry document that should link to the migration guide

## Expected Output

- `docs/reference-migration.md` — canonical migration guide grounded in the tested proof path
- `README.md` — updated documentation map/link wiring for the new migration guide
- `docs/quickstart.md` — updated cross-linking if needed so the happy path leads naturally into the migration guide

## Observability Impact

- Human-facing signals added/clarified: the canonical migration guide now points adopters to the exact public evidence surfaces (`X-Nebula-*` headers and `X-Request-ID`) plus operator-side confirmation via `GET /v1/admin/usage/ledger`.
- Inspection surfaces for future agents: `docs/reference-migration.md`, the README documentation map, the quickstart handoff into the migration guide, and `tests/test_reference_migration.py` as the executable proof source.
- Failure visibility improved: doc-verification commands now make it obvious whether the migration guide is missing, undiscoverable from main entry points, or out of alignment with the tested public-header and ledger-correlation proof path.
