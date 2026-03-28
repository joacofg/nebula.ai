import type { UsageLedgerRecord } from "@/lib/admin-api";

type RouteSignals = Record<string, unknown>;

type LedgerRequestDetailProps = {
  entry: UsageLedgerRecord | null;
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

export function LedgerRequestDetail({ entry }: LedgerRequestDetailProps) {
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

  return (
    <section className="panel space-y-4 px-6 py-5">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Request detail</div>
        <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">{entry.request_id}</h3>
        <p className="mt-2 text-sm text-slate-600">
          This persisted ledger record explains the final route, provider, fallback, cache, and policy
          outcome for the same request ID that operators first corroborate through the public response headers.
        </p>
      </div>
      <dl className="grid gap-4 sm:grid-cols-2">
        <DetailRow label="Request ID" value={entry.request_id} mono />
        <DetailRow label="Timestamp" value={formatTimestamp(entry.timestamp)} />
        <DetailRow label="Tenant" value={entry.tenant_id} mono />
        <DetailRow label="Route target" value={entry.final_route_target} />
        <DetailRow label="Requested model" value={entry.requested_model} />
        <DetailRow label="Response model" value={valueOrFallback(entry.response_model)} />
        <DetailRow label="Provider" value={valueOrFallback(entry.final_provider)} />
        <DetailRow label="Route reason" value={valueOrFallback(entry.route_reason)} />
        <DetailRow label="Policy outcome" value={valueOrFallback(entry.policy_outcome)} />
        <DetailRow label="Fallback used" value={boolLabel(entry.fallback_used)} />
        <DetailRow label="Cache hit" value={boolLabel(entry.cache_hit)} />
        <DetailRow label="Terminal status" value={entry.terminal_status} />
        <DetailRow label="Prompt tokens" value={String(entry.prompt_tokens)} />
        <DetailRow label="Completion tokens" value={String(entry.completion_tokens)} />
        <DetailRow label="Total tokens" value={String(entry.total_tokens)} />
      </dl>
      {routeSignals ? (
        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-950">Route Decision</h4>
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
