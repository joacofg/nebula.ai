import type { CalibrationEvidenceSummary, UsageLedgerRecord } from "@/lib/admin-api";
import { getHostedContractContent } from "@/lib/hosted-contract";

type RouteSignals = Record<string, unknown>;

type LedgerRequestDetailProps = {
  entry: UsageLedgerRecord | null;
  calibrationSummary?: CalibrationEvidenceSummary | null;
};

type BudgetPolicyExplanation = {
  summary: string;
  detail: string | null;
  fields: Array<{ label: string; value: string }>;
};

type CalibrationExplanation = {
  badge: string;
  summary: string;
  detail: string;
  fields: Array<{ label: string; value: string }>;
};

type RoutingInspection = {
  summary: string;
  detail: string;
  fields: Array<{ label: string; value: string }>;
};

function boolLabel(value: boolean) {
  return value ? "Yes" : "No";
}

function valueOrFallback(value: string | null | undefined) {
  return value && value.length > 0 ? value : "N/A";
}

function formatTimestamp(value: string) {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return value;
  }
  return timestamp.toLocaleString();
}

function asRouteSignals(value: UsageLedgerRecord["route_signals"]): RouteSignals | null {
  return value && typeof value === "object" ? value : null;
}

function signalValue(signals: RouteSignals | null, key: string) {
  return signals?.[key];
}

function formatBooleanSignal(value: unknown) {
  return value ? "yes" : "no";
}

function formatBudgetProximity(value: unknown) {
  const numericValue = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numericValue)) {
    return null;
  }
  return `${Math.round(numericValue * 100)}%`;
}

function formatScore(value: unknown) {
  const numericValue = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numericValue)) {
    return null;
  }
  return numericValue.toFixed(2);
}

function titleCaseToken(value: string) {
  return value
    .split(/[_-]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatReasonCounts(items: CalibrationEvidenceSummary["excluded_reasons"]) {
  if (items.length === 0) {
    return "None";
  }
  return items.map((item) => `${titleCaseToken(item.reason)} (${item.count})`).join(", ");
}

function buildCalibrationExplanation(summary: CalibrationEvidenceSummary): CalibrationExplanation {
  const latestEligible =
    summary.latest_eligible_request_at !== null
      ? formatTimestamp(summary.latest_eligible_request_at)
      : "No eligible calibrated rows yet";

  const fields: Array<{ label: string; value: string }> = [
    {
      label: "Eligible calibrated rows",
      value: `${summary.eligible_request_count} of ${summary.thin_request_threshold} needed`,
    },
    {
      label: "Latest eligible row",
      value: latestEligible,
    },
  ];

  if (summary.gated_request_count > 0) {
    fields.push({
      label: "Rollout-disabled rows",
      value: `${summary.gated_request_count} (${formatReasonCounts(summary.gated_reasons)})`,
    });
  }

  if (summary.degraded_request_count > 0) {
    fields.push({
      label: "Degraded rows",
      value: `${summary.degraded_request_count} (${formatReasonCounts(summary.degraded_reasons)})`,
    });
  }

  if (summary.excluded_request_count > 0) {
    fields.push({
      label: "Excluded rows",
      value: `${summary.excluded_request_count} (${formatReasonCounts(summary.excluded_reasons)})`,
    });
  }

  if (summary.state === "sufficient") {
    return {
      badge: "Sufficient",
      summary: "Tenant evidence is ready for calibrated routing and replay checks.",
      detail:
        "Recent ledger-backed rows meet the tenant sufficiency threshold. This supports replay readiness and explains the broader routing posture without replacing the persisted story for this request.",
      fields,
    };
  }

  if (summary.state === "stale") {
    fields.push({
      label: "Staleness threshold",
      value: `${summary.staleness_threshold_hours} hours`,
    });
    return {
      badge: "Stale",
      summary: "Tenant evidence exists, but the eligible calibrated window is stale.",
      detail:
        "The ledger has enough historical calibrated rows, but the newest eligible evidence is older than the allowed freshness window. Treat this as context for operator review, not as fresh proof for current routing behavior.",
      fields,
    };
  }

  if (summary.gated_request_count > 0 && summary.eligible_request_count === 0) {
    return {
      badge: "Rollout disabled",
      summary: "Tenant traffic is visible, but calibrated routing rollout is still operator-gated.",
      detail:
        "Recent rows show traffic while calibrated routing remained disabled. Operators can inspect this request and replay posture, but the ledger does not yet provide enough eligible calibrated evidence for live calibration decisions.",
      fields,
    };
  }

  return {
    badge: "Thin",
    summary: "Tenant evidence is still thin for calibrated routing and replay checks.",
    detail:
      "The ledger does not yet have enough eligible calibrated rows to treat tenant-level evidence as sufficient. Keep using the persisted request record as the primary proof surface while the evidence window fills in.",
    fields,
  };
}

function extractBudgetExplanation(policyOutcome: string | null | undefined): BudgetPolicyExplanation | null {
  if (!policyOutcome) {
    return null;
  }

  const fields: Array<{ label: string; value: string }> = [];
  let summary: string | null = null;
  let detail: string | null = null;

  const hardBudgetMatch = policyOutcome.match(
    /hard_budget=exceeded\(limit_usd=([^,]+),spent_usd=([^,]+),enforcement=([^\)]+)\)/,
  );
  if (hardBudgetMatch) {
    const [, limitUsd, spentUsd, enforcement] = hardBudgetMatch;
    summary = "Hard budget reached";
    fields.push({ label: "Spent at decision", value: `$${spentUsd}` });
    fields.push({ label: "Hard budget limit", value: `$${limitUsd}` });
    fields.push({ label: "Hard budget enforcement", value: titleCaseToken(enforcement) });
  }

  if (policyOutcome.includes("budget_action=downgraded_to_local")) {
    summary = "Premium traffic downgraded to local";
    detail = "Cumulative premium spend hit the tenant hard budget, so this request stayed allowed by routing to a local model instead of premium.";
    fields.push({ label: "Budget action", value: "Downgraded to local" });
  }

  const deniedMatch = policyOutcome.match(/(?:^|;)denied=([^;]+)/);
  if (deniedMatch) {
    summary = "Premium request denied by budget guardrail";
    detail = deniedMatch[1];
    fields.push({ label: "Denial reason", value: deniedMatch[1] });
  } else if (policyOutcome.startsWith("Tenant hard budget limit reached; premium routing is blocked")) {
    summary = "Premium request denied by budget guardrail";
    detail = policyOutcome;
    fields.push({ label: "Denial reason", value: policyOutcome });

    const spentMatch = policyOutcome.match(/spent_usd=([^,\)]+)/);
    const limitMatch = policyOutcome.match(/limit_usd=([^\)]+)/);
    if (spentMatch) {
      fields.push({ label: "Spent at decision", value: `$${spentMatch[1]}` });
    }
    if (limitMatch) {
      fields.push({ label: "Hard budget limit", value: `$${limitMatch[1]}` });
    }
  }

  if (policyOutcome.includes("soft_budget=exceeded")) {
    if (!summary) {
      summary = "Soft budget advisory triggered";
    }
    if (!detail) {
      detail = "Cumulative spend exceeded the advisory soft budget. Routing continued, but the request was tagged for operator visibility.";
    }
    fields.push({ label: "Soft budget status", value: "Exceeded (advisory only)" });
  }

  if (!summary && fields.length === 0) {
    return null;
  }

  return {
    summary: summary ?? "Budget policy evidence",
    detail,
    fields,
  };
}

function formatRoutingState(
  routeMode: string | null,
  calibratedRouting: boolean | null,
  degradedRouting: boolean | null,
  routeScore: number | null,
  routeReason: string | null,
) {
  if (routeMode === null && routeReason === "calibrated_routing_disabled") {
    return "rollout disabled";
  }

  const markers: string[] = [];
  if (calibratedRouting === true) {
    markers.push("calibrated");
  }
  if (degradedRouting === true) {
    markers.push("degraded");
  }

  const routeScoreLabel = routeScore === null ? null : routeScore.toFixed(2);
  const detailParts = markers.join(" / ");
  const detail = [detailParts, routeScoreLabel === null ? null : `score ${routeScoreLabel}`]
    .filter((value): value is string => Boolean(value))
    .join(", ");

  if (routeMode === null) {
    return detail.length > 0 ? `unscored (${detail})` : "unscored";
  }

  return detail.length > 0 ? `${routeMode} (${detail})` : routeMode;
}

function buildRoutingInspection(
  routeSignals: RouteSignals | null,
  routeReason: string | null,
): RoutingInspection | null {
  if (!routeSignals) {
    return null;
  }

  const routeModeRaw = signalValue(routeSignals, "route_mode");
  const routeMode = typeof routeModeRaw === "string" ? routeModeRaw : null;

  const calibratedRoutingRaw = signalValue(routeSignals, "calibrated_routing");
  const calibratedRouting = typeof calibratedRoutingRaw === "boolean" ? calibratedRoutingRaw : null;

  const degradedRoutingRaw = signalValue(routeSignals, "degraded_routing");
  const degradedRouting = typeof degradedRoutingRaw === "boolean" ? degradedRoutingRaw : null;

  const scoreComponentsValue = signalValue(routeSignals, "score_components");
  const scoreComponents =
    scoreComponentsValue && typeof scoreComponentsValue === "object"
      ? (scoreComponentsValue as Record<string, unknown>)
      : null;

  const componentTotal = scoreComponents ? formatScore(scoreComponents.total_score) : null;
  const directRouteScore = formatScore(signalValue(routeSignals, "route_score"));
  const routeScore = componentTotal ?? directRouteScore;

  const summary = formatRoutingState(
    routeMode,
    calibratedRouting,
    degradedRouting,
    routeScore === null ? null : Number(routeScore),
    routeReason,
  );

  let detail =
    "This request detail shows the persisted routing state for the selected ledger row only.";
  if (summary === "rollout disabled") {
    detail =
      "Calibrated routing was intentionally disabled for this request, so the row stays explicit about rollout state instead of looking like missing routing data.";
  } else if (summary.startsWith("degraded")) {
    detail =
      "Routing fell back to degraded scoring because replay-critical calibrated inputs were incomplete for this persisted row.";
  } else if (summary.startsWith("calibrated")) {
    detail =
      "Routing used the full calibrated signal set recorded for this request, including the additive score breakdown when present.";
  } else if (summary.startsWith("unscored")) {
    detail =
      "This row did not carry a calibrated score path. That is explicit request-level state, not a generic analytics gap.";
  }

  const fields: Array<{ label: string; value: string }> = [
    { label: "Routing state", value: summary },
  ];

  if (routeMode !== null) {
    fields.push({ label: "Route mode", value: routeMode });
  }

  if (routeScore !== null) {
    fields.push({ label: "Route score", value: routeScore });
  }

  if (scoreComponents) {
    const componentEntries: Array<[string, string]> = [
      ["Token score", formatScore(scoreComponents.token_score)],
      ["Keyword bonus", formatScore(scoreComponents.keyword_bonus)],
      ["Policy bonus", formatScore(scoreComponents.policy_bonus)],
      ["Budget penalty", formatScore(scoreComponents.budget_penalty)],
    ].filter((entry): entry is [string, string] => entry[1] !== null);

    componentEntries.forEach(([label, value]) => {
      fields.push({ label, value });
    });
  }

  return { summary, detail, fields };
}

function formatSuppressedFields(fields: string[]) {
  if (fields.length === 0) {
    return "None";
  }
  return fields.map((field) => titleCaseToken(field)).join(", ");
}

export function LedgerRequestDetail({ entry, calibrationSummary = null }: LedgerRequestDetailProps) {
  if (!entry) {
    return <div className="panel px-6 py-5 text-sm text-slate-500">Select a ledger row to inspect request detail.</div>;
  }

  const routeSignals = asRouteSignals(entry.route_signals);
  const tokenCount = signalValue(routeSignals, "token_count");
  const complexityTier = signalValue(routeSignals, "complexity_tier");
  const keywordMatch = signalValue(routeSignals, "keyword_match");
  const modelConstraint = signalValue(routeSignals, "model_constraint");
  const budgetProximity = signalValue(routeSignals, "budget_proximity");
  const budgetProximityLabel =
    budgetProximity === null || budgetProximity === undefined ? null : formatBudgetProximity(budgetProximity);
  const budgetExplanation = extractBudgetExplanation(entry.policy_outcome);
  const calibrationExplanation = calibrationSummary ? buildCalibrationExplanation(calibrationSummary) : null;
  const routingInspection = buildRoutingInspection(routeSignals, entry.route_reason);
  const { copy, reinforcement } = getHostedContractContent();

  return (
    <section className="panel space-y-4 px-6 py-5">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Request detail</div>
        <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">{entry.request_id}</h3>
        <p className="mt-2 text-sm text-slate-600">
          This persisted ledger record is the authoritative evidence row for this request ID while the row still
          exists. It explains the retained route, provider, fallback, cache, and policy outcome that operators first
          corroborate through the public response headers before reading broader tenant or hosted posture guidance
          elsewhere on this page. If governed retention cleanup later deletes the row at its persisted expiration time,
          this request detail should disappear with it rather than imply recovery, a soft-deleted archive, or hosted raw
          export.
        </p>
      </div>
      <dl className="grid gap-4 sm:grid-cols-2">
        <DetailRow label="Request ID" value={entry.request_id} mono />
        <DetailRow label="Timestamp" value={formatTimestamp(entry.timestamp)} />
        <DetailRow label="Tenant" value={entry.tenant_id} mono />
        <DetailRow label="Message type" value={entry.message_type} />
        <DetailRow label="Route target" value={entry.final_route_target} />
        <DetailRow label="Requested model" value={entry.requested_model} />
        <DetailRow label="Response model" value={valueOrFallback(entry.response_model)} />
        <DetailRow label="Provider" value={valueOrFallback(entry.final_provider)} />
        <DetailRow label="Route reason" value={valueOrFallback(entry.route_reason)} />
        <DetailRow label="Policy outcome" value={valueOrFallback(entry.policy_outcome)} />
        <DetailRow label="Evidence retention" value={entry.evidence_retention_window} />
        <DetailRow label="Evidence expires at" value={valueOrFallback(entry.evidence_expires_at)} />
        <DetailRow label="Metadata minimization" value={entry.metadata_minimization_level} />
        <DetailRow label="Suppressed metadata fields" value={formatSuppressedFields(entry.metadata_fields_suppressed)} />
        <DetailRow label="Governance source" value={entry.governance_source} />
        <DetailRow label="Fallback used" value={boolLabel(entry.fallback_used)} />
        <DetailRow label="Cache hit" value={boolLabel(entry.cache_hit)} />
        <DetailRow label="Terminal status" value={entry.terminal_status} />
        <DetailRow label="Prompt tokens" value={String(entry.prompt_tokens)} />
        <DetailRow label="Completion tokens" value={String(entry.completion_tokens)} />
        <DetailRow label="Total tokens" value={String(entry.total_tokens)} />
      </dl>
      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h4 className="text-sm font-semibold text-slate-950">Effective evidence boundary</h4>
          <span className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-sky-900">
            Row-level governance truth
          </span>
        </div>
        <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4 text-sm text-slate-700">
          <p>{reinforcement.evidenceBoundaryVocabulary.retained}</p>
          <p className="mt-3">{reinforcement.evidenceBoundaryVocabulary.suppressed}</p>
          <p className="mt-3">{reinforcement.evidenceBoundaryVocabulary.deleted}</p>
          <p className="mt-3">{reinforcement.evidenceBoundaryVocabulary.notHosted}</p>
          <p className="mt-3">{copy.hostedExportExclusion}</p>
        </div>
      </section>
      {calibrationExplanation ? (
        <section className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h4 className="text-sm font-semibold text-slate-950">Calibration evidence</h4>
            <span className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-sky-900">
              {calibrationExplanation.badge}
            </span>
          </div>
          <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Summary</div>
            <p className="mt-2 text-sm font-medium text-slate-950">{calibrationExplanation.summary}</p>
            <p className="mt-2 text-sm text-slate-600">{calibrationExplanation.detail}</p>
            <p className="mt-3 text-xs text-slate-500">{calibrationSummary?.state_reason}</p>
          </div>
          <dl className="grid gap-4 sm:grid-cols-2">
            {calibrationExplanation.fields.map((field) => (
              <DetailRow key={`${field.label}-${field.value}`} label={field.label} value={field.value} />
            ))}
          </dl>
        </section>
      ) : null}
      {budgetExplanation ? (
        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-950">Budget policy evidence</h4>
          <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Summary</div>
            <p className="mt-2 text-sm font-medium text-slate-950">{budgetExplanation.summary}</p>
            {budgetExplanation.detail ? <p className="mt-2 text-sm text-slate-600">{budgetExplanation.detail}</p> : null}
          </div>
          <dl className="grid gap-4 sm:grid-cols-2">
            {budgetExplanation.fields.map((field) => (
              <DetailRow key={`${field.label}-${field.value}`} label={field.label} value={field.value} />
            ))}
          </dl>
        </section>
      ) : null}
      {routingInspection ? (
        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-950">Routing inspection</h4>
          <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Summary</div>
            <p className="mt-2 text-sm font-medium text-slate-950">{routingInspection.summary}</p>
            <p className="mt-2 text-sm text-slate-600">{routingInspection.detail}</p>
          </div>
          <dl className="grid gap-4 sm:grid-cols-2">
            {routingInspection.fields.map((field) => (
              <DetailRow key={`${field.label}-${field.value}`} label={field.label} value={field.value} />
            ))}
          </dl>
        </section>
      ) : null}
      {routeSignals ? (
        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-950">Route signals</h4>
          <dl className="grid gap-4 sm:grid-cols-2">
            {tokenCount !== undefined ? <DetailRow label="Token count" value={String(tokenCount)} /> : null}
            {complexityTier !== undefined ? (
              <DetailRow label="Complexity tier" value={String(complexityTier)} />
            ) : null}
            {keywordMatch !== undefined ? (
              <DetailRow label="Keyword match" value={formatBooleanSignal(keywordMatch)} />
            ) : null}
            {modelConstraint !== undefined ? (
              <DetailRow label="Model constraint" value={formatBooleanSignal(modelConstraint)} />
            ) : null}
            {budgetProximityLabel ? (
              <DetailRow label="Budget proximity" value={budgetProximityLabel} />
            ) : null}
          </dl>
        </section>
      ) : null}
    </section>
  );
}

function DetailRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-border bg-white px-4 py-4">
      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</dt>
      <dd className={["mt-2 text-sm text-slate-900", mono ? "font-[var(--font-fira-code)]" : ""].join(" ")}>
        {value}
      </dd>
    </div>
  );
}
