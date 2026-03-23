import type { UsageLedgerRecord } from "@/lib/admin-api";

type PlaygroundRecordedOutcomeProps = {
  entry: UsageLedgerRecord;
};

function formatEstimatedCost(value: number | null) {
  if (value === null) {
    return "N/A";
  }
  return `$${value.toFixed(4)}`;
}

function yesNo(value: boolean) {
  return value ? "Yes" : "No";
}

function displayValue(value: string | null) {
  return value && value.trim().length > 0 ? value : "N/A";
}

export function PlaygroundRecordedOutcome({ entry }: PlaygroundRecordedOutcomeProps) {
  return (
    <section className="panel space-y-4 px-6 py-5">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
          Recorded outcome
        </div>
        <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
          Recorded outcome
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          Persisted ledger evidence for the same request after Nebula records the final route, provider,
          fallback, and policy outcome.
        </p>
      </div>

      <dl className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <OutcomeRow label="Terminal status" value={entry.terminal_status} />
        <OutcomeRow label="Route target" value={entry.final_route_target} />
        <OutcomeRow label="Provider" value={displayValue(entry.final_provider)} />
        <OutcomeRow label="Route reason" value={displayValue(entry.route_reason)} />
        <OutcomeRow label="Policy outcome" value={displayValue(entry.policy_outcome)} />
        <OutcomeRow label="Fallback used" value={yesNo(entry.fallback_used)} />
        <OutcomeRow label="Cache hit" value={yesNo(entry.cache_hit)} />
        <OutcomeRow label="Prompt tokens" value={String(entry.prompt_tokens)} />
        <OutcomeRow label="Completion tokens" value={String(entry.completion_tokens)} />
        <OutcomeRow label="Total tokens" value={String(entry.total_tokens)} />
        <OutcomeRow label="Estimated cost" value={formatEstimatedCost(entry.estimated_cost)} />
      </dl>
    </section>
  );
}

function OutcomeRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-white px-4 py-4">
      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</dt>
      <dd className="mt-2 text-sm text-slate-900">{value}</dd>
    </div>
  );
}
