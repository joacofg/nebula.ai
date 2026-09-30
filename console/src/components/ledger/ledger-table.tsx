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
    return <div className="panel px-6 py-5 text-sm text-ink-4">Loading usage ledger...</div>;
  }

  if (rows.length === 0) {
    return <div className="panel px-6 py-5 text-sm text-ink-4">No usage ledger rows match these filters.</div>;
  }

  return (
    <div className="panel overflow-hidden">
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-canvas text-ink-3">
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
                className={selected ? "bg-mark-soft/70 ring-1 ring-inset ring-mark-line" : "hover:bg-canvas"}
              >
                <td className="px-4 py-3 align-top">{new Date(row.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3 align-top">
                  <button
                    type="button"
                    onClick={() => onSelectRow(row.request_id)}
                    aria-pressed={selected}
                    aria-label={selectionLabel}
                    className={selected ? "group w-full rounded-xl border border-mark-line bg-surface/90 px-3 py-2 text-left shadow-xs transition focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-mark" : "group w-full rounded-xl border border-transparent px-3 py-2 text-left transition hover:border-line hover:bg-surface focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-mark"}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-(--font-fira-code) text-xs text-ink-2">{row.request_id}</span>
                      {selected ? (
                        <span className="rounded-full border border-mark-line bg-mark-soft px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-mark">
                          Current investigation
                        </span>
                      ) : (
                        <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-4 transition group-hover:text-ink-3">
                          Select request
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-xs text-ink-4">
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
