import type { UsageLedgerRecord } from "@/lib/admin-api";

type LedgerRequestDetailProps = {
  entry: UsageLedgerRecord | null;
};

function boolLabel(value: boolean) {
  return value ? "Yes" : "No";
}

function displayValue(value: string | null) {
  return value && value.trim().length > 0 ? value : "N/A";
}

export function LedgerRequestDetail({ entry }: LedgerRequestDetailProps) {
  if (!entry) {
    return <div className="panel px-6 py-5 text-sm text-slate-500">Select a ledger row to inspect request detail.</div>;
  }

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
        <DetailRow label="Tenant" value={entry.tenant_id} mono />
        <DetailRow label="Route target" value={entry.final_route_target} />
        <DetailRow label="Provider" value={displayValue(entry.final_provider)} />
        <DetailRow label="Route reason" value={displayValue(entry.route_reason)} />
        <DetailRow label="Policy outcome" value={displayValue(entry.policy_outcome)} />
        <DetailRow label="Fallback used" value={boolLabel(entry.fallback_used)} />
        <DetailRow label="Cache hit" value={boolLabel(entry.cache_hit)} />
        <DetailRow label="Terminal status" value={entry.terminal_status} />
        <DetailRow label="Prompt tokens" value={String(entry.prompt_tokens)} />
        <DetailRow label="Completion tokens" value={String(entry.completion_tokens)} />
        <DetailRow label="Total tokens" value={String(entry.total_tokens)} />
      </dl>
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
