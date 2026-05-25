---
estimated_steps: 3
estimated_files: 3
skills_used: []
---

# T01: Wire resilience metadata into runtime health cards

Why: S01/S02 already emit a richer additive dependency contract, but the console currently narrows it away and the health cards silently drop most operator-relevant resilience fields, which blocks R088 on the main operator surface.

Do: Expand the shared console runtime-health typing in `console/src/lib/admin-api.ts` to model the additive resilience keys while remaining compatible with older payloads. Update `console/src/components/health/runtime-health-cards.tsx` so cards render bounded resilience metadata alongside existing status/detail and retention-lifecycle metrics: dependency class, lifecycle/recovering state, serving effect, reason code, enabled where useful, and last failure/recovery timestamps when present. Preserve the current optional-degradation banner and request-first page framing; do not introduce a new dashboard, severity matrix, or hosted-authoritative wording.

Done when: The runtime health card component can render serving-critical fail-closed, serving-optional continuity-limited, and recovering examples with visible resilience metadata, while legacy payloads that only contain `status` / `required` / `detail` still render correctly and existing retention metrics remain intact.

## Inputs

- `console/src/lib/admin-api.ts`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/components/health/runtime-health-cards.test.tsx`
- `.gsd/milestones/M010/slices/S03/S03-RESEARCH.md`

## Expected Output

- `console/src/lib/admin-api.ts`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/components/health/runtime-health-cards.test.tsx`

## Verification

npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx

## Observability Impact

Makes resilience fields visible on the existing dependency health cards so operators can inspect failed dependency class, degraded mode, and recovery context directly from Observability.
