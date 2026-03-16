"use client";

import { useEffect, useState } from "react";

import { useQuery } from "@tanstack/react-query";

import { RuntimeHealthCards } from "@/components/health/runtime-health-cards";
import { LedgerFilters } from "@/components/ledger/ledger-filters";
import { LedgerRequestDetail } from "@/components/ledger/ledger-request-detail";
import { LedgerTable } from "@/components/ledger/ledger-table";
import { listTenants, listUsageLedger } from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";

export default function ObservabilityPage() {
  const { adminKey } = useAdminSession();
  const [tenantId, setTenantId] = useState("");
  const [routeTarget, setRouteTarget] = useState("");
  const [terminalStatus, setTerminalStatus] = useState("");
  const [fromTimestamp, setFromTimestamp] = useState("");
  const [toTimestamp, setToTimestamp] = useState("");
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const ledgerFilters = {
    tenantId,
    routeTarget,
    terminalStatus,
    fromTimestamp,
    toTimestamp,
  };
  // terminal_status is encoded by the shared admin API client from this filter object.
  const ledgerQuery = useQuery({
    queryKey: queryKeys.usageLedger(ledgerFilters),
    queryFn: () => listUsageLedger(adminKey ?? "", ledgerFilters),
    enabled: Boolean(adminKey),
  });
  const runtimeHealthQuery = useQuery({
    queryKey: queryKeys.runtimeHealth,
    queryFn: async () => {
      const response = await fetch("/api/runtime/health", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Unable to load runtime health.");
      }
      return (await response.json()) as {
        dependencies: Record<string, { status: string; required: boolean; detail: string }>;
      };
    },
  });

  useEffect(() => {
    if (!selectedRequestId && ledgerQuery.data?.length) {
      setSelectedRequestId(ledgerQuery.data[0].request_id);
    }
  }, [ledgerQuery.data, selectedRequestId]);

  const selectedEntry =
    ledgerQuery.data?.find((entry) => entry.request_id === selectedRequestId) ?? ledgerQuery.data?.[0] ?? null;

  return (
    <section className="space-y-6">
      <header className="panel px-6 py-5">
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Observability</div>
        <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
          Usage ledger
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Inspect recorded request outcomes by tenant, route target, terminal status, and time window.
        </p>
      </header>

      <LedgerFilters
        tenants={tenantsQuery.data ?? []}
        tenantId={tenantId}
        routeTarget={routeTarget}
        terminalStatus={terminalStatus}
        fromTimestamp={fromTimestamp}
        toTimestamp={toTimestamp}
        onTenantIdChange={setTenantId}
        onRouteTargetChange={setRouteTarget}
        onTerminalStatusChange={setTerminalStatus}
        onFromTimestampChange={setFromTimestamp}
        onToTimestampChange={setToTimestamp}
        onRefresh={() => {
          void ledgerQuery.refetch();
        }}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.8fr)]">
        {ledgerQuery.isError ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
            {ledgerQuery.error instanceof Error ? ledgerQuery.error.message : "Unable to load the usage ledger."}
          </div>
        ) : (
          <LedgerTable
            rows={ledgerQuery.data ?? []}
            selectedRequestId={selectedEntry?.request_id ?? null}
            onSelectRow={(requestId) => setSelectedRequestId(requestId)}
            isLoading={ledgerQuery.isLoading}
          />
        )}

        <LedgerRequestDetail entry={selectedEntry} />
      </div>

      <section className="space-y-4">
        <header className="panel px-6 py-5">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Dependency health</div>
          <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
            Dependency health
          </h2>
        </header>

        {runtimeHealthQuery.isError ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
            {runtimeHealthQuery.error instanceof Error
              ? runtimeHealthQuery.error.message
              : "Unable to load dependency health."}
          </div>
        ) : (
          <RuntimeHealthCards
            dependencies={runtimeHealthQuery.data?.dependencies ?? {}}
            isLoading={runtimeHealthQuery.isLoading}
          />
        )}
      </section>
    </section>
  );
}
