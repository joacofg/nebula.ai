import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  getHostedContractContent,
  excludedByDefault,
  freshnessStates,
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

  it("would throw if an unknown schema property appeared", () => {
    // Verify the parity check is active by confirming all schema keys are covered
    const schemaKeys = Object.keys(schema.properties);
    const content = getHostedContractContent();
    const mappedKeys = content.defaultExportedData.map((f) => f.key);
    expect(new Set(mappedKeys)).toEqual(new Set(schemaKeys));
  });
});
