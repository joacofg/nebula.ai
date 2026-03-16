import type { TenantRecord } from "@/lib/admin-api";

type LedgerFiltersProps = {
  tenants: TenantRecord[];
  tenantId: string;
  routeTarget: string;
  terminalStatus: string;
  fromTimestamp: string;
  toTimestamp: string;
  onTenantIdChange: (value: string) => void;
  onRouteTargetChange: (value: string) => void;
  onTerminalStatusChange: (value: string) => void;
  onFromTimestampChange: (value: string) => void;
  onToTimestampChange: (value: string) => void;
  onRefresh: () => void;
};

const ROUTE_TARGET_OPTIONS = ["cache", "local", "premium", "denied"];
const TERMINAL_STATUS_OPTIONS = [
  "completed",
  "cache_hit",
  "fallback_completed",
  "policy_denied",
  "provider_error",
];

export function LedgerFilters({
  tenants,
  tenantId,
  routeTarget,
  terminalStatus,
  fromTimestamp,
  toTimestamp,
  onTenantIdChange,
  onRouteTargetChange,
  onTerminalStatusChange,
  onFromTimestampChange,
  onToTimestampChange,
  onRefresh,
}: LedgerFiltersProps) {
  return (
    <section className="panel px-6 py-5">
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <label>
          <span className="field-label">Tenant</span>
          <select className="field-input" value={tenantId} onChange={(event) => onTenantIdChange(event.target.value)}>
            <option value="">All tenants</option>
            {tenants.map((tenant) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span className="field-label">Route target</span>
          <select
            className="field-input"
            value={routeTarget}
            onChange={(event) => onRouteTargetChange(event.target.value)}
          >
            <option value="">All routes</option>
            {ROUTE_TARGET_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span className="field-label">Terminal status</span>
          <select
            className="field-input"
            value={terminalStatus}
            onChange={(event) => onTerminalStatusChange(event.target.value)}
          >
            <option value="">All statuses</option>
            {TERMINAL_STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span className="field-label">From</span>
          <input
            className="field-input"
            type="datetime-local"
            value={fromTimestamp}
            onChange={(event) => onFromTimestampChange(event.target.value)}
          />
        </label>

        <label>
          <span className="field-label">To</span>
          <input
            className="field-input"
            type="datetime-local"
            value={toTimestamp}
            onChange={(event) => onToTimestampChange(event.target.value)}
          />
        </label>

        <div className="flex items-end">
          <button type="button" className="secondary-button w-full" onClick={onRefresh}>
            Refresh
          </button>
        </div>
      </div>
    </section>
  );
}
