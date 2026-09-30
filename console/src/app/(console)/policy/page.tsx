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
import { EmptyState, LoadingRows } from "@/components/system/state";
import { PolicyForm } from "@/components/policy/policy-form";
import { queryKeys } from "@/lib/query-keys";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function PolicyPage() {
  const queryClient = useQueryClient();
  const { adminKey } = useAdminSession();
  const [selectedTenantId, setSelectedTenantId] = useState<string>("");
  const [latestSimulation, setLatestSimulation] = useState<PolicySimulationResponse | null>(null);

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  useEffect(() => {
    if (!selectedTenantId && tenantsQuery.data?.length) {
      setSelectedTenantId(tenantsQuery.data[0].id);
    }
  }, [selectedTenantId, tenantsQuery.data]);

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
        throw new Error("Operator session missing.");
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
        throw new Error("Operator session missing.");
      }
      return simulateTenantPolicy(adminKey, selectedTenantId, {
        candidate_policy: payload,
        limit: 50,
        changed_sample_limit: 5,
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
      onChange={(event) => setSelectedTenantId(event.target.value)}
    >
      {tenantsQuery.data?.map((tenant) => (
        <option key={tenant.id} value={tenant.id}>
          {tenant.name}
        </option>
      ))}
    </select>
  );
  const header = <PageHeader title="Política" cells={[{ label: "Tenant", value: tenantSelect }]} />;

  if (tenantsQuery.isLoading || optionsQuery.isLoading || policyQuery.isLoading) {
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
    const error =
      (tenantsQuery.error as Error | undefined)?.message ||
      (optionsQuery.error as Error | undefined)?.message ||
      (policyQuery.error as Error | undefined)?.message ||
      "No se pudo cargar la política.";
    return (
      <section>
        {header}
        <div className="px-6 py-6">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
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
          <EmptyState title="No hay tenants. Crear uno en Tenants." />
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
            ? (simulationMutation.error as Error | undefined)?.message ?? "No se pudo simular el borrador."
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
