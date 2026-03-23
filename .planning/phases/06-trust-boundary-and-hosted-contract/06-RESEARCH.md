# Phase 6: Trust Boundary and Hosted Contract - Research

**Researched:** 2026-03-21
**Domain:** Hybrid hosted/self-hosted contract definition, disclosure UX, and contract-source architecture
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Hosted positioning
- The hosted control plane should be framed as the recommended operating model for pilots, while remaining optional for self-hosted customers.
- Nebula should preserve the message that a fully self-hosted deployment is still a real and complete product, not a crippled mode.
- The primary value claim for the hosted layer should be easier onboarding and clearer fleet visibility, with safer limited remote operations as a supporting benefit rather than the lead pitch.
- The product should state clearly that the hosted layer is not in the request-serving path and does not become authoritative for local runtime enforcement.

### Data export contract
- The default hosted-data posture should be minimal-by-default and metadata-only.
- Hosted-visible default fields may include deployment identity, operator-assigned labels, environment, Nebula version, capability flags, registration timestamps, last-seen/freshness timestamps, coarse dependency summary, and remote-action audit summaries.
- Hosted-visible default data must exclude raw prompts, responses, provider credentials, raw usage-ledger rows, tenant secrets, and authoritative runtime policy state.
- Richer diagnostics should be explicit and separate from the default contract. If later phases add diagnostic export or bundle upload flows, those should be operator-initiated and clearly framed as exceptions to the default boundary.

### Status language
- Hosted status must never collapse into a single generic "healthy" claim.
- The primary hosted-plane status should describe control-plane freshness using `connected`, `degraded`, `stale`, and `offline` semantics.
- Local runtime health should remain a separate, explicitly reported signal rather than being implied by hosted freshness.
- Hosted copy should prefer truthful uncertainty over optimism: timestamps, last-reported wording, and reason codes should make it clear when Nebula is showing reported local state versus current hosted connectivity.

### Disclosure surfaces
- The trust boundary should be visible in three places: linking/onboarding flow, hosted deployment detail surfaces, and canonical documentation.
- The linking flow should explain the outbound-only relationship and the default metadata contract before a deployment is connected.
- Hosted deployment detail views should include a durable "what this deployment shares" or trust-boundary disclosure surface, not just a documentation link.
- Canonical docs should carry the longer-form explanation in the architecture and self-hosting narratives so pilot evaluators can verify the boundary outside the UI.

### Claude's Discretion
- Exact field names, schema naming, and payload shape for the hosted metadata contract.
- Exact UI treatment of the trust-boundary disclosure card, banners, or callouts, as long as the boundary stays persistent and unambiguous.
- Exact wording for status reason codes and the split between top-level badge text versus supporting explanatory copy.

### Deferred Ideas (OUT OF SCOPE)
- Exact enrollment UX and identity lifecycle details — Phase 7.
- Hosted inventory pages, compatibility badges, and freshness implementation details — Phase 8.
- The first concrete remote-management action and its audit mechanics — Phase 9.
- Broader hosted auth, RBAC, self-serve signup, billing, and enterprise packaging — future phases.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TRST-01 | Hosted control plane clearly distinguishes hosted metadata from self-hosted runtime-enforced state in the product UI and architecture narrative. | Use one canonical hosted-contract model, a shared disclosure-content module, explicit freshness-vs-runtime wording, and static disclosure surfaces in both docs and Next.js pages. |
| TRST-02 | Security model states exactly what data leaves the self-hosted environment by default and excludes raw prompts, responses, provider credentials, and authoritative runtime policy state. | Define an explicit allowlist export schema plus an explicit excluded-data section, generate a machine-readable schema artifact from the backend model, and test exclusions in pytest plus UI/docs rendering in frontend tests. |
</phase_requirements>

## Summary

Phase 6 should be planned as a contract-first phase, not a networked hosted-product phase. The codebase already has the right shape for that: backend truth lives in Pydantic models, the console uses Next.js App Router with clear page/layout boundaries, and the repo already ships architecture and self-hosting docs that operators treat as canonical. The safest plan is to freeze the hosted export contract in one backend source of truth, derive a stable schema/example artifact from it, and reuse that same contract in disclosure copy and future hosted phases.

The biggest risk is drift, not implementation complexity. If the export field list, status semantics, and exclusions are written separately in Python, TypeScript, and Markdown, Phase 7-10 work will fork the trust model immediately. The plan should therefore centralize three things now: the metadata allowlist, the excluded-data list, and the freshness vocabulary. Hosted surfaces in this phase should be static or documentation-backed surfaces only; enrollment, live heartbeats, inventory, and remote actions remain later phases.

**Primary recommendation:** Define the hosted/default-export contract as a Pydantic model and explicit exclusions module in `src/nebula/models/`, publish it through repo docs plus a static Next.js trust-boundary surface, and lock it with backend, Vitest, and Playwright tests before Phase 7 starts.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pydantic` | `>=2.8.0,<3.0.0` | Canonical hosted export models, enums, and schema generation | The repo already uses Pydantic for authoritative external contracts; `BaseModel.model_json_schema()` avoids hand-maintained schema drift. |
| `fastapi` | `>=0.115.0,<1.0.0` | Backend location for contract artifacts and future hosted-policy narrative endpoints if needed | Existing HTTP boundary and model validation layer; no reason to introduce a second contract service. |
| `next` | `^15.2.2` | Static/public disclosure page and reusable hosted trust-boundary components | The console already uses App Router; pages/layouts and metadata are first-class patterns in the current app. |
| `react` / `react-dom` | `^19.0.0` | Disclosure-card composition and future hosted-surface reuse | Already established in the console; Phase 6 should extend that surface, not create a parallel frontend stack. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tailwindcss` | `^3.4.17` | Reuse the current control-plane visual language for boundary cards/callouts | Use for persistent disclosure UI so it matches existing compact console patterns. |
| `@tanstack/react-query` | `^5.66.9` | Optional client fetch for a generated contract artifact or future detail panel | Use only if a Phase 6 page consumes a local JSON/schema endpoint; avoid it for static copy-only pages. |
| `vitest` | `^3.0.8` | Component/page tests for disclosure copy and hosted/local distinction | Use for trust-boundary cards, static page rendering, and copy regression tests. |
| `@playwright/test` | `^1.51.0` | End-to-end verification that disclosure surfaces remain visible and unambiguous | Use for page-level trust-boundary regression, especially pre-link/onboarding copy. |
| `pytest` | `>=8.2.0,<9.0.0` | Contract tests for export-field allowlist and exclusion guarantees | Use to lock the schema and prevent accidental additions like prompt payloads or credentials. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic canonical contract model | Handwritten Markdown tables or duplicated TS types | Faster initially, but guarantees drift between docs, UI, and future enrollment/heartbeat payloads. |
| Existing Next.js console app for disclosure surfaces | A separate hosted frontend or docs engine | Premature scope expansion; Phase 6 needs truthful surfaces, not a new app boundary. |
| Explicit freshness enum and reason codes | One generic hosted “healthy” badge | Simpler copy, but directly violates the locked requirement to avoid overstating runtime health. |

**Installation:**
```bash
npm --prefix console install
pip install -e .[dev]
```

## Architecture Patterns

### Recommended Project Structure
```text
src/
└── nebula/
    ├── models/
    │   └── hosted_contract.py      # Canonical default-export contract and enums
    ├── services/
    │   └── hosted_contract.py      # Optional artifact serialization/helpers only
    └── api/
        └── routes/
            └── hosted_contract.py  # Optional local artifact endpoint if Phase 6 needs one

console/
└── src/
    ├── app/
    │   └── trust-boundary/
    │       └── page.tsx            # Static/public contract narrative outside auth-gated console group
    ├── components/
    │   └── hosted/
    │       ├── trust-boundary-card.tsx
    │       └── data-sharing-table.tsx
    └── content/
        └── trust-boundary.ts       # Shared copy tokens, labels, exclusions, reason-code text

docs/
├── architecture.md                 # Extended with hosted/local authority split
└── self-hosting.md                 # Extended with exact default exported data and exclusions
```

### Pattern 1: Canonical Contract Model
**What:** Define one backend model for the default hosted export payload and related enums, then generate JSON Schema or example artifacts from it.
**When to use:** Always for field names, freshness semantics, and excluded-data guarantees that future phases must inherit.
**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
from typing import Literal

from pydantic import BaseModel, Field

FreshnessState = Literal["connected", "degraded", "stale", "offline"]


class HostedDependencySummary(BaseModel):
    status: Literal["ready", "degraded", "not_ready", "unknown"]
    required: bool
    detail: str


class HostedDeploymentMetadata(BaseModel):
    deployment_id: str
    labels: dict[str, str] = Field(default_factory=dict)
    environment: str
    nebula_version: str
    capability_flags: list[str] = Field(default_factory=list)
    registered_at: str
    last_seen_at: str | None = None
    freshness: FreshnessState
    dependency_summary: dict[str, HostedDependencySummary] = Field(default_factory=dict)
    remote_action_audit_summary: dict[str, int] = Field(default_factory=dict)
```

### Pattern 2: Shared Disclosure Content Module
**What:** Keep the operator-visible allowlist, exclusions, and freshness language in a shared TS content module consumed by pages and cards.
**When to use:** For any static/public trust-boundary surface and later hosted detail pages.
**Example:**
```typescript
// Source: https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts
export const hostedContractSections = {
  defaultExportedData: [
    "Deployment identity",
    "Operator-assigned labels",
    "Environment",
    "Nebula version",
    "Capability flags",
    "Registration timestamps",
    "Last-seen and freshness timestamps",
    "Coarse dependency summary",
    "Remote-action audit summaries",
  ],
  excludedByDefault: [
    "Raw prompts",
    "Raw responses",
    "Provider credentials",
    "Raw usage-ledger rows",
    "Tenant secrets",
    "Authoritative runtime policy state",
  ],
} as const;
```

### Pattern 3: Public Static Trust-Boundary Route
**What:** Publish the contract narrative on a server-rendered App Router page outside the auth-gated `(console)` group.
**When to use:** In Phase 6, because there is no real hosted app yet but operators still need a UI surface before linking.
**Example:**
```typescript
// Source: https://nextjs.org/docs/app/api-reference/functions/generate-metadata
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Nebula Hosted Trust Boundary",
  description: "What the optional hosted control plane can see by default and what stays local.",
};

export default function TrustBoundaryPage() {
  return <main>{/* disclosure cards and contract tables */}</main>;
}
```

### Anti-Patterns to Avoid
- **Duplicate contract sources:** Do not maintain separate field lists in Python models, TS types, and Markdown by hand.
- **Hosted health overclaiming:** Do not use “healthy” as the top-level hosted state. Use freshness semantics plus explicit “last reported” wording.
- **Phase leakage into enrollment or inventory:** Do not build actual linking flows, live deployment records, or remote actions in Phase 6.
- **Implicit exclusions:** Do not say “metadata only” without a concrete excluded-data list. The excluded set must be operator-readable.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Export contract definition | Ad hoc dict payloads and Markdown-only tables | Pydantic models plus generated schema/example artifacts | Future phases need stable field names, enums, and tests against accidental contract expansion. |
| Disclosure copy reuse | Repeated JSX strings across pages/cards/docs | Shared content module plus doc sections sourced from the same canonical list | Trust boundaries fail when copy drifts by one field or one exception. |
| Hosted freshness semantics | Bespoke badge logic per surface | One shared enum and mapping table | Prevents some pages from implying runtime authority while others stay precise. |
| Browser test bootstrapping | Custom shell scripts for static page checks | Existing Playwright `webServer` config | The repo already has the correct end-to-end harness. |

**Key insight:** The hard part in this phase is not rendering a card or writing prose. It is ensuring the contract remains singular and reusable when enrollment, heartbeat, inventory, and remote actions arrive later.

## Common Pitfalls

### Pitfall 1: Contract Drift Across Docs, UI, and Future Payloads
**What goes wrong:** The backend allowlist says one thing, docs say another, and the hosted UI exposes a third interpretation.
**Why it happens:** Each surface gets authored independently because Phase 6 feels “mostly docs.”
**How to avoid:** Make the backend contract authoritative, export a stable schema/example artifact, and snapshot-test the frontend disclosure lists against the same source material.
**Warning signs:** New field names appear in docs without a matching model change; future phases invent labels not present in the contract model.

### Pitfall 2: Freshness Language Becomes Health Language
**What goes wrong:** Hosted connectivity wording starts implying current local runtime health.
**Why it happens:** UI teams collapse multiple states into a simpler success/failure badge.
**How to avoid:** Reserve `connected/degraded/stale/offline` for hosted freshness only, and phrase local state as “last reported runtime status” or equivalent.
**Warning signs:** Copy uses “deployment healthy” without a local runtime source or timestamp.

### Pitfall 3: Static Disclosure Surfaces Get Buried
**What goes wrong:** The contract only exists in docs, or only behind future hosted pages, so operators cannot inspect it before linking.
**Why it happens:** The team waits for Phase 7/8 to mount the content in-product.
**How to avoid:** Add a Phase 6 public/static route now and structure the disclosure card for reuse in later linking and deployment-detail surfaces.
**Warning signs:** The only Phase 6 artifact is a paragraph in `docs/architecture.md`.

### Pitfall 4: Exclusions Are Framed as Marketing, Not Contract
**What goes wrong:** “We don’t send prompts by default” becomes vague and non-testable.
**Why it happens:** Security language is written as positioning copy instead of a precise allowlist/denylist.
**How to avoid:** Express exclusions as exact field classes with tests that fail when those fields are added to the default export model.
**Warning signs:** Words like “typically,” “generally,” or “may” appear in the exclusion statement.

## Code Examples

Verified patterns from official sources:

### Generate a Schema Artifact From the Canonical Model
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
from nebula.models.hosted_contract import HostedDeploymentMetadata

HOSTED_CONTRACT_SCHEMA = HostedDeploymentMetadata.model_json_schema()
```

### Use a Static App Router Page for the Disclosure Surface
```typescript
// Source: https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts
import { TrustBoundaryCard } from "@/components/hosted/trust-boundary-card";
import { hostedContractSections } from "@/content/trust-boundary";

export default function TrustBoundaryPage() {
  return (
    <section className="space-y-6">
      <TrustBoundaryCard
        exported={hostedContractSections.defaultExportedData}
        excluded={hostedContractSections.excludedByDefault}
      />
    </section>
  );
}
```

### Keep Frontend Unit Tests in `jsdom`
```typescript
// Source: https://vitest.dev/guide/environment.html
import { render, screen } from "@testing-library/react";

import TrustBoundaryPage from "@/app/trust-boundary/page";

test("renders the excluded-by-default data list", () => {
  render(<TrustBoundaryPage />);
  expect(screen.getByText("Provider credentials")).toBeInTheDocument();
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Narrative-only “security boundary” docs | Machine-readable contract plus in-product disclosure surfaces | Current Nebula v2.0 planning direction, 2026-03 | Planners should allocate work for a canonical schema artifact, not just prose updates. |
| Generic hosted health badge | Freshness enum with timestamps and reason codes | Locked in Phase 6 context, 2026-03-18 | UI tasks must treat hosted visibility and local authority as separate concepts. |
| One product story centered only on self-hosted runtime | “Self-hosted with an optional hosted control plane” | Current milestone decision, 2026-03-18 | Docs and surfaces must add hosted framing without weakening the self-hosted-first message. |

**Deprecated/outdated:**
- Generic “healthy” copy for hosted-plane status.
- Docs-only trust-boundary explanation with no persistent UI disclosure surface.
- Duplicated field lists maintained separately in backend models and frontend copy.

## Open Questions

1. **Where should the Phase 6 UI surface live before hosted auth and enrollment exist?**
   - What we know: The current Next app already has a public root route and an auth-gated `(console)` group.
   - What's unclear: Whether product wants the disclosure route in the same app or only in docs.
   - Recommendation: Put it in the existing Next app as a public static route outside `(console)` and mirror the narrative in docs.

2. **Should the generated schema artifact be committed or generated only in tests/build?**
   - What we know: Later phases will need the exact contract for enrollment, inventory, and remote-action summaries.
   - What's unclear: Whether another consumer needs a committed JSON file now.
   - Recommendation: Commit a generated JSON schema or example artifact if docs/UI link to it directly; otherwise generate in tests and keep the backend model authoritative.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` (`>=8.2.0,<9.0.0`), `vitest` (`^3.0.8`), `@playwright/test` (`^1.51.0`) |
| Config file | `pyproject.toml`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| Quick run command | `pytest tests/test_hosted_contract.py -x && npm --prefix console run test -- --run trust-boundary` |
| Full suite command | `pytest && npm --prefix console run test && npm --prefix console run e2e` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRST-01 | Hosted surfaces explicitly separate hosted metadata/freshness from locally authoritative runtime state | unit + e2e | `npm --prefix console run test -- --run trust-boundary` and `npm --prefix console run e2e -- trust-boundary.spec.ts` | ❌ Wave 0 |
| TRST-02 | Default export contract includes only allowlisted metadata and excludes prompts, responses, credentials, raw ledger rows, tenant secrets, and authoritative runtime policy state | unit | `pytest tests/test_hosted_contract.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_hosted_contract.py -x` or `npm --prefix console run test -- --run trust-boundary`
- **Per wave merge:** `pytest && npm --prefix console run test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_hosted_contract.py` — covers TRST-02 and schema drift guards
- [ ] `console/src/components/hosted/trust-boundary-card.test.tsx` — covers TRST-01 disclosure copy and separation language
- [ ] `console/src/app/trust-boundary/page.test.tsx` — covers public page rendering and excluded-data list
- [ ] `console/e2e/trust-boundary.spec.ts` — covers page-level visibility before auth-gated routes

## Sources

### Primary (HIGH confidence)
- Repository sources:
  - `.planning/phases/06-trust-boundary-and-hosted-contract/06-CONTEXT.md` - locked decisions, disclosure surfaces, and out-of-scope items
  - `.planning/REQUIREMENTS.md` - `TRST-01`, `TRST-02`, and out-of-scope contract boundaries
  - `.planning/ROADMAP.md` - Phase 6 goals, success criteria, and plan split
  - `.planning/PROJECT.md` - self-hosted-first product framing and v2.0 milestone constraints
  - `docs/architecture.md` - current self-hosted architecture narrative and authority boundaries
  - `docs/self-hosting.md` - canonical runbook that must stay truthful when hosted remains optional
  - `console/src/app/layout.tsx` and `console/src/app/(console)/layout.tsx` - current App Router structure and auth boundary
  - `console/src/components/shell/operator-shell.tsx` - existing control-plane tone and information density
  - `src/nebula/models/governance.py` - current authoritative schema pattern
  - `console/src/lib/admin-api.ts` - current frontend contract duplication pattern to avoid extending blindly
- Official docs:
  - https://docs.pydantic.dev/latest/concepts/models/ - Pydantic model pattern and schema generation support
  - https://nextjs.org/docs/app/building-your-application/routing/pages-and-layouts - App Router page/layout structure
  - https://nextjs.org/docs/app/api-reference/functions/generate-metadata - metadata export pattern for App Router pages
  - https://vitest.dev/guide/environment.html - `jsdom` environment guidance for browser-like component tests
  - https://playwright.dev/docs/test-webserver - built-in `webServer` pattern already matching the repo config

### Secondary (MEDIUM confidence)
- None needed beyond repository evidence and official docs.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Derived from the repo’s actual manifests/config plus official framework docs.
- Architecture: HIGH - Strongly constrained by locked Phase 6 decisions and existing code/doc insertion points.
- Pitfalls: HIGH - Directly supported by prior phase decisions, repo patterns, and explicit Phase 6 success criteria.

**Research date:** 2026-03-21
**Valid until:** 2026-04-20
