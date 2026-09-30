import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
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

const ROUTE_TARGET_OPTIONS = ["cache", "local", "premium", "denied", "embeddings"];
const TERMINAL_STATUS_OPTIONS = [
  "completed",
  "cache_hit",
  "fallback_completed",
  "policy_denied",
  "provider_error",
  "rate_limited",
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
  const cell = "flex min-w-[150px] flex-1 flex-col gap-1 border-l border-line px-4 py-2.5 first:border-l-0";
  const wide = "flex min-w-[210px] flex-1 flex-col gap-1 border-l border-line px-4 py-2.5";
  const control =
    "h-9 w-full rounded-[2px] border border-line bg-surface px-2 text-[15px] text-ink transition-colors focus:border-ink";
  return (
    <div className="flex flex-wrap items-stretch border-b border-line bg-surface" role="group" aria-label="Filtros del ledger">
      <label className={cell}>
        <span className="font-label text-[13px] font-medium text-ink-3">Tenant</span>
        <select className={control} value={tenantId} onChange={(event) => onTenantIdChange(event.target.value)}>
          <option value="">Todos los tenants</option>
          {tenants.map((tenant) => (
            <option key={tenant.id} value={tenant.id}>
              {tenant.name}
            </option>
          ))}
        </select>
      </label>

      <label className={cell}>
        <span className="font-label text-[13px] font-medium text-ink-3">Ruta</span>
        <select className={control} value={routeTarget} onChange={(event) => onRouteTargetChange(event.target.value)}>
          <option value="">Todas</option>
          {ROUTE_TARGET_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className={cell}>
        <span className="font-label text-[13px] font-medium text-ink-3">Estado</span>
        <select className={control} value={terminalStatus} onChange={(event) => onTerminalStatusChange(event.target.value)}>
          <option value="">Todos</option>
          {TERMINAL_STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className={wide}>
        <span className="font-label text-[13px] font-medium text-ink-3">Desde</span>
        <input className={control} type="datetime-local" value={fromTimestamp} onChange={(event) => onFromTimestampChange(event.target.value)} />
      </label>

      <label className={wide}>
        <span className="font-label text-[13px] font-medium text-ink-3">Hasta</span>
        <input className={control} type="datetime-local" value={toTimestamp} onChange={(event) => onToTimestampChange(event.target.value)} />
      </label>

      <div className="flex items-end border-l border-line px-4 py-2.5">
        <Button type="button" variant="outline" onClick={onRefresh} className="h-9">
          <RefreshCw aria-hidden className="size-4" />
          Actualizar
        </Button>
      </div>
    </div>
  );
}
