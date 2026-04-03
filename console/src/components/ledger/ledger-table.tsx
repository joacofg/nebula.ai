import type { UsageLedgerRecord } from "@/lib/admin-api";

type LedgerTableProps = {
  rows: UsageLedgerRecord[];
  selectedRequestId: string | null;
  onSelectRow: (requestId: string) => void;
  isLoading: boolean;
};

function formatEstimatedCost(value: number | null) {
  return value === null ? "N/A" : `$${value.toFixed(4)}`;
}

function formatLatency(value: number | null) {
  return value === null ? "N/A" : `${Math.round(value)} ms`;
}

export function LedgerTable({ rows, selectedRequestId, onSelectRow, isLoading }: LedgerTableProps) {
  if (isLoading) {
    return <div className="panel px-6 py-5 text-sm text-slate-500">Loading usage ledger...</div>;
  }

  if (rows.length === 0) {
    return <div className="panel px-6 py-5 text-sm text-slate-500">No usage ledger rows match these filters.</div>;
  }

  return (
    <div className="panel overflow-hidden">
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            <th className="px-4 py-3 font-semibold">Timestamp</th>
            <th className="px-4 py-3 font-semibold">Request ID</th>
            <th className="px-4 py-3 font-semibold">Tenant</th>
            <th className="px-4 py-3 font-semibold">Route target</th>
            <th className="px-4 py-3 font-semibold">Provider</th>
            <th className="px-4 py-3 font-semibold">Status</th>
            <th className="px-4 py-3 font-semibold">Latency</th>
            <th className="px-4 py-3 font-semibold">Estimated cost</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const selected = row.request_id === selectedRequestId;
            const selectionLabel = selected ? `Current investigation: ${row.request_id}` : `Inspect request ${row.request_id}`;

            return (
              <tr
                key={row.request_id}
                aria-selected={selected}
                className={selected ? "bg-sky-50/70 ring-1 ring-inset ring-sky-200" : "hover:bg-slate-50"}
              >
                <td className="px-4 py-3 align-top">{new Date(row.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3 align-top">
                  <button
                    type="button"
                    onClick={() => onSelectRow(row.request_id)}
                    aria-pressed={selected}
                    aria-label={selectionLabel}
                    className={selected ? "group w-full rounded-xl border border-sky-200 bg-white/90 px-3 py-2 text-left shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500" : "group w-full rounded-xl border border-transparent px-3 py-2 text-left transition hover:border-slate-200 hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-[var(--font-fira-code)] text-xs text-slate-700">{row.request_id}</span>
                      {selected ? (
                        <span className="rounded-full border border-sky-200 bg-sky-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-800">
                          Current investigation
                        </span>
                      ) : (
                        <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400 transition group-hover:text-slate-500">
                          Select request
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                      {selected
                        ? "Primary request for the detail view below."
                        : "Promote this request into the primary detail view."}
                    </p>
                  </button>
                </td>
                <td className="px-4 py-3 align-top">{row.tenant_id}</td>
                <td className="px-4 py-3 align-top">{row.final_route_target}</td>
                <td className="px-4 py-3 align-top">{row.final_provider ?? "N/A"}</td>
                <td className="px-4 py-3 align-top">{row.terminal_status}</td>
                <td className="px-4 py-3 align-top">{formatLatency(row.latency_ms)}</td>
                <td className="px-4 py-3 align-top">{formatEstimatedCost(row.estimated_cost)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
