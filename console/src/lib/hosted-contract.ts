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
// Reinforcement vocabulary and guardrails
// ---------------------------------------------------------------------------

export const reinforcementContract = {
  allowedDescriptiveClaims: [
    "Hosted summaries are metadata-backed and descriptive only.",
    "Hosted fleet posture describes what deployments most recently reported, not what the local runtime is enforcing right now.",
    "Hosted freshness indicates report recency, not serving-time health or request success.",
    "Hosted onboarding establishes deployment identity and operator visibility without moving request-serving or policy authority into the hosted plane.",
    "Hosted remote actions stay bounded to audited deployment-credential rotation and related audit visibility.",
  ],
  prohibitedAuthorityClaims: [
    "Do not say the hosted plane serves traffic or sits in the request-serving path.",
    "Do not say the hosted plane has local runtime authority.",
    "Do not say the hosted plane enforces tenant policy, routing, fallback, or provider selection.",
    "Do not say the hosted plane holds provider credentials, raw prompts, raw responses, or tenant secrets by default.",
    "Do not describe hosted freshness or fleet posture as authoritative health for serving traffic.",
  ],
  operatorReadingGuidance: [
    "Read hosted fleet posture as an operator summary derived from deployment metadata exports.",
    "Use freshness and dependency summaries to prioritize investigation, then confirm serving-time behavior from the local runtime and its observability surfaces.",
    "Treat drawer-level freshness and dependency details as supporting evidence for that fleet posture summary, not as hosted authority over current runtime health.",
    "Treat hosted remote-action availability as bounded operational assistance, not broad remote control.",
  ],
  boundedActionPhrasing: {
    label: "Audited credential rotation only",
    description:
      "Deployment-bound hosted actions are limited to audited credential rotation and related status visibility; they never imply tenant-policy, routing, fallback, or provider-credential authority.",
  },
} as const;

// ---------------------------------------------------------------------------
// Copy strings
// ---------------------------------------------------------------------------

export const trustBoundaryCopy = {
  heading: "What this deployment shares",
  metadataOnly: "Metadata-only by default",
  pilotIntro:
    "Hosted onboarding creates deployment identity and fleet visibility without moving request serving or runtime policy into the hosted plane.",
  onboardingHeading: "Pilot onboarding flow",
  onboardingBody:
    "Create a deployment slot in the hosted plane, exchange a short-lived enrollment token from the self-hosted gateway, then continue with a deployment-scoped hosted-link credential.",
  outageHeading: "Hosted outage behavior",
  outageBody:
    "If the hosted control plane is unreachable, Nebula keeps serving with local policy and local provider access. Hosted freshness simply ages toward stale or offline until heartbeats resume.",
  remoteLimitsHeading: "Remote-management safety limits",
  remoteLimitsBody:
    "v2.0 allows one audited rotate_deployment_credential action only. It never changes tenant policy, provider credentials, prompts, or responses, and it fails closed when the deployment is stale, offline, unlinked, revoked, unsupported, or disallowed by local policy.",
  freshnessWarning: "Hosted freshness is not local runtime authority.",
  notInPath: "Nebula's hosted control plane is not in the request-serving path.",
  excludedHeading: "Excluded by default",
  footnote: "Richer diagnostics must be operator-initiated exceptions to this default contract.",
  hostedExportExclusion:
    "Hosted export still excludes raw usage-ledger rows; operators must confirm serving-time behavior from local runtime surfaces.",
} as const;

function assertNonEmptyArray<T>(value: readonly T[], fieldName: string) {
  if (value.length < 1) {
    throw new Error(`${fieldName} must not be empty.`);
  }
}

function assertReinforcementContract() {
  const { allowedDescriptiveClaims, prohibitedAuthorityClaims, operatorReadingGuidance, boundedActionPhrasing } =
    reinforcementContract;

  assertNonEmptyArray(
    allowedDescriptiveClaims,
    "reinforcementContract.allowedDescriptiveClaims",
  );
  assertNonEmptyArray(
    prohibitedAuthorityClaims,
    "reinforcementContract.prohibitedAuthorityClaims",
  );
  assertNonEmptyArray(
    operatorReadingGuidance,
    "reinforcementContract.operatorReadingGuidance",
  );

  const requiredAllowedPhrases = [
    "metadata-backed and descriptive only",
    "fleet posture",
    "request-serving",
    "freshness indicates report recency",
    "credential rotation",
  ];

  for (const phrase of requiredAllowedPhrases) {
    if (!allowedDescriptiveClaims.some((claim) => claim.includes(phrase))) {
      throw new Error(
        `reinforcementContract.allowedDescriptiveClaims must include a claim containing \"${phrase}\".`
      );
    }
  }

  const requiredProhibitedPhrases = [
    "serves traffic",
    "request-serving path",
    "local runtime authority",
    "tenant policy, routing, fallback, or provider selection",
    "provider credentials, raw prompts, raw responses, or tenant secrets",
  ];

  for (const phrase of requiredProhibitedPhrases) {
    if (!prohibitedAuthorityClaims.some((claim) => claim.includes(phrase))) {
      throw new Error(
        `reinforcementContract.prohibitedAuthorityClaims must include a guardrail containing \"${phrase}\".`
      );
    }
  }

  const requiredGuidancePhrases = [
    "operator summary",
    "local runtime",
    "bounded operational assistance",
  ];

  for (const phrase of requiredGuidancePhrases) {
    if (!operatorReadingGuidance.some((claim) => claim.includes(phrase))) {
      throw new Error(
        `reinforcementContract.operatorReadingGuidance must include guidance containing \"${phrase}\".`
      );
    }
  }

  if (!boundedActionPhrasing.label.includes("credential rotation")) {
    throw new Error(
      'reinforcementContract.boundedActionPhrasing.label must reference "credential rotation".'
    );
  }

  const boundedDescription = boundedActionPhrasing.description;
  const requiredBoundedDescriptionPhrases = [
    "audited credential rotation",
    "status visibility",
    "tenant-policy",
    "routing",
    "fallback",
    "provider-credential authority",
  ];

  for (const phrase of requiredBoundedDescriptionPhrases) {
    if (!boundedDescription.includes(phrase)) {
      throw new Error(
        `reinforcementContract.boundedActionPhrasing.description must include \"${phrase}\".`
      );
    }
  }
}

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
  reinforcement: typeof reinforcementContract;
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

  assertReinforcementContract();

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
    reinforcement: reinforcementContract,
  };
}
