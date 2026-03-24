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
            return (
              <tr
                key={row.request_id}
                className={selected ? "cursor-pointer bg-sky-50" : "cursor-pointer hover:bg-slate-50"}
                onClick={() => onSelectRow(row.request_id)}
              >
                <td className="px-4 py-3">{new Date(row.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3 font-[var(--font-fira-code)] text-xs text-slate-700">{row.request_id}</td>
                <td className="px-4 py-3">{row.tenant_id}</td>
                <td className="px-4 py-3">{row.final_route_target}</td>
                <td className="px-4 py-3">{row.final_provider ?? "N/A"}</td>
                <td className="px-4 py-3">{row.terminal_status}</td>
                <td className="px-4 py-3">{formatLatency(row.latency_ms)}</td>
                <td className="px-4 py-3">{formatEstimatedCost(row.estimated_cost)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
