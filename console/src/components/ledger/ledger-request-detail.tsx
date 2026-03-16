import type { UsageLedgerRecord } from "@/lib/admin-api";

type LedgerRequestDetailProps = {
  entry: UsageLedgerRecord | null;
};

function boolLabel(value: boolean) {
  return value ? "Yes" : "No";
}

export function LedgerRequestDetail({ entry }: LedgerRequestDetailProps) {
  if (!entry) {
    return <div className="panel px-6 py-5 text-sm text-slate-500">Select a ledger row to inspect request detail.</div>;
  }

  return (
    <section className="panel space-y-4 px-6 py-5">
      <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Request detail</div>
      <h3 className="font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">{entry.request_id}</h3>
      <dl className="grid gap-4">
        <DetailRow label="Provider" value={entry.final_provider ?? "N/A"} />
        <DetailRow label="Route reason" value={entry.route_reason ?? "N/A"} />
        <DetailRow label="Policy outcome" value={entry.policy_outcome ?? "N/A"} />
        <DetailRow label="Fallback used" value={boolLabel(entry.fallback_used)} />
        <DetailRow label="Cache hit" value={boolLabel(entry.cache_hit)} />
        <DetailRow label="Prompt tokens" value={String(entry.prompt_tokens)} />
        <DetailRow label="Completion tokens" value={String(entry.completion_tokens)} />
        <DetailRow label="Total tokens" value={String(entry.total_tokens)} />
      </dl>
    </section>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-white px-4 py-4">
      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</dt>
      <dd className="mt-2 text-sm text-slate-900">{value}</dd>
    </div>
  );
}
