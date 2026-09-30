"use client";

import { useEffect, useState } from "react";

import { useQuery } from "@tanstack/react-query";

import { CacheSummary } from "@/components/observability/cache-summary";
import { CalibrationSummary } from "@/components/observability/calibration-summary";
import { Recommendations } from "@/components/observability/recommendations";
import { PageHeader } from "@/components/system/page-header";
import { LoadingRows } from "@/components/system/state";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RuntimeHealthCards } from "@/components/health/runtime-health-cards";
import { LedgerFilters } from "@/components/ledger/ledger-filters";
import { LedgerRequestDetail } from "@/components/ledger/ledger-request-detail";
import { LedgerTable } from "@/components/ledger/ledger-table";
import { getTenantRecommendations, listTenants, listUsageLedger } from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
import { ErrorAlert } from "@/components/system/state";

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

  useEffect(() => {
    if (!tenantId && tenantsQuery.data?.length) {
      setTenantId(tenantsQuery.data[0].id);
    }
  }, [tenantId, tenantsQuery.data]);

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
      const response = await fetch("/api/runtime/health", {
        cache: "no-store",
        headers: {
          "X-Nebula-Admin-Key": adminKey ?? "",
        },
      });
      if (!response.ok) {
        throw new Error("No se pudo cargar la salud de las dependencias.");
      }
      return (await response.json()) as {
        dependencies: Record<string, import("@/lib/admin-api").RuntimeHealthDependency>;
      };
    },
    enabled: Boolean(adminKey),
  });

  const recommendationsQuery = useQuery({
    queryKey: queryKeys.tenantRecommendations(tenantId || "unselected"),
    queryFn: () => getTenantRecommendations(adminKey ?? "", tenantId),
    enabled: Boolean(adminKey) && tenantId.length > 0,
  });

  useEffect(() => {
    if (!selectedRequestId && ledgerQuery.data?.length) {
      setSelectedRequestId(ledgerQuery.data[0].request_id);
    }
  }, [ledgerQuery.data, selectedRequestId]);

  const selectedEntry =
    ledgerQuery.data?.find((entry) => entry.request_id === selectedRequestId) ?? ledgerQuery.data?.[0] ?? null;

  const tenantName = tenantsQuery.data?.find((tenant) => tenant.id === tenantId)?.name ?? "Todos los tenants";
  const rows = ledgerQuery.data ?? [];
  const totalCost = rows.reduce((sum, row) => sum + (row.estimated_cost ?? 0), 0);
  const tabTrigger =
    "h-10 flex-none rounded-none border-0 px-4 text-[15px] font-semibold text-ink-3 data-active:text-ink after:bg-mark group-data-horizontal/tabs:after:bottom-[-1px]";

  return (
    <section>
      <PageHeader
        title="Observabilidad"
        cells={[
          { label: "Tenant", value: tenantName },
          { label: "Pedidos", value: ledgerQuery.data ? String(rows.length) : "—" },
          { label: "Costo", value: ledgerQuery.data ? `USD ${totalCost.toFixed(4)}` : "—" },
        ]}
      />
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
          void recommendationsQuery.refetch();
        }}
      />
      {tenantsQuery.isError ? (
        <div className="px-6 pt-4">
          <ErrorAlert error={tenantsQuery.error} fallback="No se pudieron cargar los tenants." />
        </div>
      ) : null}

      <div className="grid border-b border-line xl:grid-cols-[minmax(0,1fr)_400px]">
        <div className="min-w-0 px-6 py-5">
          {ledgerQuery.isError ? (
            <ErrorAlert error={ledgerQuery.error} fallback="No se pudo cargar el ledger." />
          ) : (
            <LedgerTable
              rows={rows}
              selectedRequestId={selectedEntry?.request_id ?? null}
              onSelectRow={(requestId) => setSelectedRequestId(requestId)}
              isLoading={ledgerQuery.isLoading}
            />
          )}
        </div>
        <div className="min-w-0 border-t border-line px-6 py-5 xl:border-t-0 xl:border-l">
          <LedgerRequestDetail entry={selectedEntry} />
        </div>
      </div>

      <div className="px-6 py-5">
        <Tabs defaultValue="recommendations">
          <TabsList variant="line" aria-label="Contexto del tenant" className="h-10 w-full justify-start gap-0 overflow-x-auto overflow-y-hidden border-b border-line p-0 *:shrink-0">
            <TabsTrigger value="recommendations" className={tabTrigger}>Recomendaciones</TabsTrigger>
            <TabsTrigger value="cache" className={tabTrigger}>Caché</TabsTrigger>
            <TabsTrigger value="calibration" className={tabTrigger}>Calibración</TabsTrigger>
            <TabsTrigger value="dependencies" className={tabTrigger}>Dependencias</TabsTrigger>
          </TabsList>
          <TabsContent value="recommendations" className="pt-5">
            {recommendationsQuery.isError ? (
              <ErrorAlert error={recommendationsQuery.error} fallback="No se pudieron cargar las recomendaciones." />
            ) : recommendationsQuery.isLoading ? (
              <LoadingRows rows={3} label="Cargando recomendaciones" />
            ) : recommendationsQuery.data ? (
              <Recommendations bundle={recommendationsQuery.data} />
            ) : (
              <p className="m-0 text-sm text-ink-3">Elegir un tenant para ver sus recomendaciones.</p>
            )}
          </TabsContent>
          <TabsContent value="cache" className="pt-5">
            {recommendationsQuery.data ? (
              <CacheSummary cache={recommendationsQuery.data.cache_summary} />
            ) : (
              <p className="m-0 text-sm text-ink-3">Elegir un tenant para ver su caché.</p>
            )}
          </TabsContent>
          <TabsContent value="calibration" className="pt-5">
            {recommendationsQuery.data ? (
              <CalibrationSummary summary={recommendationsQuery.data.calibration_summary} />
            ) : (
              <p className="m-0 text-sm text-ink-3">Elegir un tenant para ver su calibración.</p>
            )}
          </TabsContent>
          <TabsContent value="dependencies" className="pt-5">
            {runtimeHealthQuery.isError ? (
              <ErrorAlert error={runtimeHealthQuery.error} fallback="No se pudo cargar la salud de las dependencias." />
            ) : (
              <RuntimeHealthCards
                dependencies={runtimeHealthQuery.data?.dependencies ?? {}}
                isLoading={runtimeHealthQuery.isLoading}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}
