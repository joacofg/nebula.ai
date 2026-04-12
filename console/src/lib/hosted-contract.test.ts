import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  getHostedContractContent,
  excludedByDefault,
  freshnessStates,
  reinforcementContract,
} from "@/lib/hosted-contract";

// Load the canonical schema directly for parity assertions
const schemaPath = resolve(__dirname, "../../../docs/hosted-default-export.schema.json");
const schema = JSON.parse(readFileSync(schemaPath, "utf-8")) as {
  properties: Record<string, unknown>;
  title: string;
  [k: string]: unknown;
};

describe("hosted-contract content module", () => {
  it("resolves exactly 12 exported fields in schema property order", () => {
    const content = getHostedContractContent();
    expect(content.defaultExportedData).toHaveLength(12);

    const schemaKeys = Object.keys(schema.properties);
    const contentKeys = content.defaultExportedData.map((f) => f.key);
    expect(contentKeys).toEqual(schemaKeys);
  });

  it("maps every schema property to a non-empty label", () => {
    const content = getHostedContractContent();
    for (const field of content.defaultExportedData) {
      expect(field.label).toBeTruthy();
      expect(typeof field.label).toBe("string");
    }
  });

  it("freshness keys match the schema freshness_status enum", () => {
    const freshnessProperty = schema.properties.freshness_status as {
      enum: string[];
    };
    const schemaEnum = freshnessProperty.enum;
    const moduleKeys = freshnessStates.map((s) => s.key);

    expect(moduleKeys).toEqual(schemaEnum);
    expect(schemaEnum).toEqual(["connected", "degraded", "stale", "offline"]);
  });

  it("excludes exactly the 6 sensitive data classes", () => {
    expect(excludedByDefault).toEqual([
      "Raw prompts",
      "Raw responses",
      "Provider credentials",
      "Raw usage-ledger rows",
      "Tenant secrets",
      "Authoritative runtime policy state",
    ]);
  });

  it("returns all required copy strings", () => {
    const content = getHostedContractContent();
    expect(content.copy.heading).toBe("What this deployment shares");
    expect(content.copy.metadataOnly).toBe("Metadata-only by default");
    expect(content.copy.pilotIntro).toBe(
      "Hosted onboarding creates deployment identity and fleet visibility without moving request serving or runtime policy into the hosted plane."
    );
    expect(content.copy.onboardingHeading).toBe("Pilot onboarding flow");
    expect(content.copy.onboardingBody).toBe(
      "Create a deployment slot in the hosted plane, exchange a short-lived enrollment token from the self-hosted gateway, then continue with a deployment-scoped hosted-link credential."
    );
    expect(content.copy.outageHeading).toBe("Hosted outage behavior");
    expect(content.copy.outageBody).toBe(
      "If the hosted control plane is unreachable, Nebula keeps serving with local policy and local provider access. Hosted freshness simply ages toward stale or offline until heartbeats resume."
    );
    expect(content.copy.remoteLimitsHeading).toBe(
      "Remote-management safety limits"
    );
    expect(content.copy.remoteLimitsBody).toBe(
      "v2.0 allows one audited rotate_deployment_credential action only. It never changes tenant policy, provider credentials, prompts, or responses, and it fails closed when the deployment is stale, offline, unlinked, revoked, unsupported, or disallowed by local policy."
    );
    expect(content.copy.freshnessWarning).toBe(
      "Hosted freshness is not local runtime authority."
    );
    expect(content.copy.notInPath).toBe(
      "Nebula's hosted control plane is not in the request-serving path."
    );
    expect(content.copy.excludedHeading).toBe("Excluded by default");
    expect(content.copy.footnote).toBe(
      "Richer diagnostics must be operator-initiated exceptions to this default contract."
    );
  });

  it("locks the hosted reinforcement vocabulary and authority guardrails", () => {
    const content = getHostedContractContent();

    expect(content.reinforcement).toEqual(reinforcementContract);
    expect(content.reinforcement.allowedDescriptiveClaims).toEqual([
      "Hosted summaries are metadata-backed and descriptive only.",
      "Hosted fleet posture describes what deployments most recently reported, not what the local runtime is enforcing right now.",
      "Hosted freshness indicates report recency, not serving-time health or request success.",
      "Hosted onboarding establishes deployment identity and operator visibility without moving request-serving or policy authority into the hosted plane.",
      "Hosted remote actions stay bounded to audited deployment-credential rotation and related audit visibility.",
    ]);
    expect(content.reinforcement.evidenceBoundaryVocabulary).toEqual({
      retained: "Retained request detail stays local to the persisted ledger row while that governed row still exists.",
      suppressed:
        "Suppressed means governance removed or never wrote specific metadata fields, so those fields are no longer available from the ledger later.",
      deleted:
        "Deleted means governed retention removed the entire row at expiration; Nebula should not imply recovery, soft-delete archives, or hidden raw exports afterward.",
      notHosted:
        "Not hosted means the hosted control plane does not receive raw usage-ledger rows and cannot replace the local row as request-level evidence.",
    });
    expect(content.reinforcement.prohibitedAuthorityClaims).toEqual([
      "Do not say the hosted plane serves traffic or sits in the request-serving path.",
      "Do not say the hosted plane has local runtime authority.",
      "Do not say the hosted plane enforces tenant policy, routing, fallback, or provider selection.",
      "Do not say the hosted plane holds provider credentials, raw prompts, raw responses, or tenant secrets by default.",
      "Do not describe hosted freshness or fleet posture as authoritative health for serving traffic.",
    ]);
    expect(content.reinforcement.operatorReadingGuidance).toEqual([
      "Read hosted fleet posture as an operator summary derived from deployment metadata exports.",
      "Use freshness and dependency summaries to prioritize investigation, then confirm serving-time behavior from the local runtime and its observability surfaces.",
      "Treat drawer-level freshness and dependency details as supporting evidence for that fleet posture summary, not as hosted authority over current runtime health.",
      "Treat hosted remote-action availability as bounded operational assistance, not broad remote control.",
    ]);
    expect(content.reinforcement.boundedActionPhrasing).toEqual({
      label: "Audited credential rotation only",
      description:
        "Deployment-bound hosted actions are limited to audited credential rotation and related status visibility; they never imply tenant-policy, routing, fallback, or provider-credential authority.",
    });
  });

  it("fails fast if reinforcement guardrails drift away from required phrases", () => {
    const content = getHostedContractContent();

    expect(
      content.reinforcement.allowedDescriptiveClaims.some((claim) =>
        claim.includes("metadata-backed and descriptive only")
      )
    ).toBe(true);
    expect(
      content.reinforcement.allowedDescriptiveClaims.some((claim) =>
        claim.includes("fleet posture")
      )
    ).toBe(true);
    expect(
      content.reinforcement.allowedDescriptiveClaims.some((claim) =>
        claim.includes("freshness indicates report recency")
      )
    ).toBe(true);
    expect(
      content.reinforcement.prohibitedAuthorityClaims.some((claim) =>
        claim.includes("request-serving path")
      )
    ).toBe(true);
    expect(
      content.reinforcement.prohibitedAuthorityClaims.some((claim) =>
        claim.includes("local runtime authority")
      )
    ).toBe(true);
    expect(
      content.reinforcement.prohibitedAuthorityClaims.some((claim) =>
        claim.includes("tenant policy, routing, fallback, or provider selection")
      )
    ).toBe(true);
    expect(
      content.reinforcement.operatorReadingGuidance.some((claim) =>
        claim.includes("local runtime")
      )
    ).toBe(true);
    expect(content.reinforcement.evidenceBoundaryVocabulary.retained).toContain(
      "persisted ledger row"
    );
    expect(content.reinforcement.evidenceBoundaryVocabulary.suppressed).toContain(
      "no longer available from the ledger"
    );
    expect(content.reinforcement.evidenceBoundaryVocabulary.deleted).toContain(
      "soft-delete archives"
    );
    expect(content.reinforcement.evidenceBoundaryVocabulary.notHosted).toContain(
      "does not receive raw usage-ledger rows"
    );
    expect(content.reinforcement.boundedActionPhrasing.label).toContain(
      "credential rotation"
    );
    expect(content.reinforcement.boundedActionPhrasing.description).toContain(
      "related status visibility"
    );
  });

  it("would throw if an unknown schema property appeared", () => {
    // Verify the parity check is active by confirming all schema keys are covered
    const schemaKeys = Object.keys(schema.properties);
    const content = getHostedContractContent();
    const mappedKeys = content.defaultExportedData.map((f) => f.key);
    expect(new Set(mappedKeys)).toEqual(new Set(schemaKeys));
  });
});
