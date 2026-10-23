"use client";

import { useEffect, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getPolicyOptions,
  getTenantPolicy,
  listTenants,
  simulateTenantPolicy,
  updateTenantPolicy,
  type PolicySimulationResponse,
  type TenantPolicy,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { PageHeader } from "@/components/system/page-header";
import Link from "next/link";

import { EmptyState, ErrorAlert, errorMessage, LoadingRows } from "@/components/system/state";
import { PolicyForm } from "@/components/policy/policy-form";
import { queryKeys } from "@/lib/query-keys";
import { useSelectedTenant } from "@/lib/selected-tenant";

/** Recent ledger rows a simulation compares against, and the most changed rows the gateway returns. */
const SIMULATION_WINDOW = 50;

export default function PolicyPage() {
  const queryClient = useQueryClient();
  const { adminKey } = useAdminSession();
  const [latestSimulation, setLatestSimulation] = useState<PolicySimulationResponse | null>(null);

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const { tenantId, setTenantId } = useSelectedTenant(tenantsQuery.data);
  const selectedTenantId = tenantId ?? "";

  useEffect(() => {
    setLatestSimulation(null);
  }, [selectedTenantId]);

  const policyQuery = useQuery({
    queryKey: queryKeys.tenantPolicy(selectedTenantId || "unselected"),
    queryFn: () => getTenantPolicy(adminKey ?? "", selectedTenantId),
    enabled: Boolean(adminKey) && selectedTenantId.length > 0,
  });

  const optionsQuery = useQuery({
    queryKey: queryKeys.policyOptions,
    queryFn: () => getPolicyOptions(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: TenantPolicy) => {
      if (!adminKey) {
        throw new Error("Falta la sesión de admin.");
      }
      return updateTenantPolicy(adminKey, selectedTenantId, payload);
    },
    onSuccess: async () => {
      setLatestSimulation(null);
      await queryClient.invalidateQueries({ queryKey: queryKeys.tenantPolicy(selectedTenantId) });
    },
  });

  const simulationMutation = useMutation({
    mutationFn: async (payload: TenantPolicy) => {
      if (!adminKey) {
        throw new Error("Falta la sesión de admin.");
      }
      // Every changed row of the window comes back (the gateway returns at most 50 changed rows),
      // so the preview's headline counts all of them; the preview lists the first few.
      return simulateTenantPolicy(adminKey, selectedTenantId, {
        candidate_policy: payload,
        limit: SIMULATION_WINDOW,
        changed_sample_limit: SIMULATION_WINDOW,
      });
    },
    onSuccess: (result) => {
      setLatestSimulation(result);
    },
  });

  const tenantSelect = (
    <select
      id="policy-tenant-select"
      aria-label="Tenant"
      className="h-9 min-w-56 rounded-[2px] border border-line bg-surface px-2 text-[15px] font-semibold text-ink"
      value={selectedTenantId}
      onChange={(event) => setTenantId(event.target.value)}
    >
      {tenantsQuery.data?.map((tenant) => (
        <option key={tenant.id} value={tenant.id}>
          {tenant.name}
        </option>
      ))}
    </select>
  );
  const header = <PageHeader title="Política" cells={[{ label: "Tenant", value: tenantSelect }]} />;

  // `isPending`, not `isLoading`: a query that has no data yet but is not fetching (paused while
  // the gateway is unreachable) is still waiting, not an empty list or an unchosen tenant. The
  // policy query is disabled until a tenant is chosen, so it only counts once there is one.
  const waitingForPolicy = selectedTenantId.length > 0 && policyQuery.isPending;
  if (tenantsQuery.isPending || optionsQuery.isPending || waitingForPolicy) {
    return (
      <section>
        {header}
        <div className="px-6 py-6">
          <LoadingRows rows={8} label="Cargando la política" />
        </div>
      </section>
    );
  }

  if (tenantsQuery.isError || optionsQuery.isError || policyQuery.isError) {
    return (
      <section>
        {header}
        <div className="px-6 py-6">
          <ErrorAlert
            error={tenantsQuery.error ?? optionsQuery.error ?? policyQuery.error}
            fallback="No se pudo cargar la política."
          />
        </div>
      </section>
    );
  }

  const selectedTenant = tenantsQuery.data?.find((tenant) => tenant.id === selectedTenantId) ?? null;
  if (!selectedTenant || !policyQuery.data || !optionsQuery.data) {
    return (
      <section>
        {header}
        <div className="px-6 py-6">
          {(tenantsQuery.data ?? []).length === 0 ? (
            <EmptyState
              title="No hay tenants."
              action={
                <Link href="/tenants" className="text-sm font-semibold text-ink underline underline-offset-4 hover:text-mark">
                  Crear tenant
                </Link>
              }
            />
          ) : (
            <EmptyState title="Elegir un tenant." />
          )}
        </div>
      </section>
    );
  }

  return (
    <section>
      {header}
      <PolicyForm
        key={selectedTenantId}
        tenantName={selectedTenant.name}
        initialPolicy={policyQuery.data}
        options={optionsQuery.data}
        isSaving={saveMutation.isPending}
        isSimulating={simulationMutation.isPending}
        simulationResult={latestSimulation}
        simulationError={
          simulationMutation.isError
            ? errorMessage(simulationMutation.error, "No se pudo simular el borrador.")
            : null
        }
        onSimulate={async (payload) => {
          await simulationMutation.mutateAsync(payload);
        }}
        onSave={async (payload) => {
          await saveMutation.mutateAsync(payload);
        }}
      />
    </section>
  );
}
