/**
 * Shared trust-boundary content module.
 *
 * Sources its exported-field list from the canonical backend schema artifact
 * (`docs/hosted-default-export.schema.json`) so the UI never hand-maintains
 * a second allowlist.
 */

import schemaJson from "../../../docs/hosted-default-export.schema.json";

// ---------------------------------------------------------------------------
// Schema-to-label mapping (exact order of HostedDeploymentMetadata properties)
// ---------------------------------------------------------------------------

const exportedFieldLabels: Record<string, string> = {
  deployment_id: "Deployment identity",
  display_name: "Deployment display name",
  environment: "Environment",
  labels: "Operator-assigned labels",
  nebula_version: "Nebula version",
  capability_flags: "Capability flags",
  registered_at: "Registration timestamp",
  last_seen_at: "Last-seen timestamp",
  freshness_status: "Hosted freshness status",
  freshness_reason: "Hosted freshness reason",
  dependency_summary: "Coarse dependency summary",
  remote_action_summary: "Remote-action audit summary",
} as const;

// ---------------------------------------------------------------------------
// Excluded data classes
// ---------------------------------------------------------------------------

export const excludedByDefault = [
  "Raw prompts",
  "Raw responses",
  "Provider credentials",
  "Raw usage-ledger rows",
  "Tenant secrets",
  "Authoritative runtime policy state",
] as const;

// ---------------------------------------------------------------------------
// Freshness states
// ---------------------------------------------------------------------------

export const freshnessStates = [
  { key: "connected", description: "Hosted control plane is receiving current deployment reports." },
  { key: "degraded", description: "Hosted control plane is reachable but reports reduced freshness or partial dependency trouble." },
  { key: "stale", description: "Hosted control plane is showing last-reported data older than the expected heartbeat window." },
  { key: "offline", description: "Hosted control plane has no current connectivity signal from the deployment." },
] as const;

// ---------------------------------------------------------------------------
// Copy strings
// ---------------------------------------------------------------------------

export const trustBoundaryCopy = {
  heading: "What this deployment shares",
  metadataOnly: "Metadata-only by default",
  freshnessWarning: "Hosted freshness is not local runtime authority.",
  notInPath: "Nebula's hosted control plane is not in the request-serving path.",
  excludedHeading: "Excluded by default",
  footnote: "Richer diagnostics must be operator-initiated exceptions to this default contract.",
} as const;

// ---------------------------------------------------------------------------
// Schema-backed content helper
// ---------------------------------------------------------------------------

export interface ExportedField {
  key: string;
  label: string;
}

export interface HostedContractContent {
  defaultExportedData: ExportedField[];
  excludedByDefault: readonly string[];
  freshnessStates: readonly { key: string; description: string }[];
  copy: typeof trustBoundaryCopy;
}

export function getHostedContractContent(): HostedContractContent {
  const schema = schemaJson as { properties?: Record<string, unknown>; title?: string };
  const schemaKeys = Object.keys(schema.properties ?? {});

  // Fail fast if any schema key is missing from the mapping
  for (const key of schemaKeys) {
    if (!(key in exportedFieldLabels)) {
      throw new Error(
        `Schema property "${key}" has no label mapping in hosted-contract.ts. ` +
        `Update exportedFieldLabels to include this field.`
      );
    }
  }

  // Fail fast if any mapping key is not in the schema
  for (const key of Object.keys(exportedFieldLabels)) {
    if (!schemaKeys.includes(key)) {
      throw new Error(
        `Label mapping "${key}" does not exist in hosted-default-export.schema.json. ` +
        `Remove it from exportedFieldLabels or update the schema.`
      );
    }
  }

  // Parity check: freshness_status enum must match freshnessStates keys
  const freshnessProperty = schema.properties?.freshness_status as
    | { enum?: string[] }
    | undefined;
  const schemaFreshnessEnum = freshnessProperty?.enum ?? [];
  const expectedFreshnessKeys = freshnessStates.map((s) => s.key);

  if (
    schemaFreshnessEnum.length !== expectedFreshnessKeys.length ||
    !schemaFreshnessEnum.every((k, i) => k === expectedFreshnessKeys[i])
  ) {
    throw new Error(
      `Freshness enum mismatch. Schema has [${schemaFreshnessEnum.join(", ")}] ` +
      `but expected [${expectedFreshnessKeys.join(", ")}].`
    );
  }

  // Build the exported data list in schema property order
  const defaultExportedData: ExportedField[] = schemaKeys.map((key) => ({
    key,
    label: exportedFieldLabels[key],
  }));

  return {
    defaultExportedData,
    excludedByDefault,
    freshnessStates,
    copy: trustBoundaryCopy,
  };
}
