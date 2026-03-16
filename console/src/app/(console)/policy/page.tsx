"use client";

import { useEffect, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getPolicyOptions,
  getTenantPolicy,
  listTenants,
  updateTenantPolicy,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { PolicyForm } from "@/components/policy/policy-form";
import { queryKeys } from "@/lib/query-keys";

export default function PolicyPage() {
  const queryClient = useQueryClient();
  const { adminKey } = useAdminSession();
  const [selectedTenantId, setSelectedTenantId] = useState<string>("");

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

  const mutation = useMutation({
    mutationFn: async (payload: Awaited<ReturnType<typeof getTenantPolicy>>) => {
      if (!adminKey) {
        throw new Error("Operator session missing.");
      }
      return updateTenantPolicy(adminKey, selectedTenantId, payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.tenantPolicy(selectedTenantId) });
    },
  });

  if (tenantsQuery.isLoading || optionsQuery.isLoading || policyQuery.isLoading) {
    return <div className="panel px-6 py-8 text-sm text-slate-500">Loading policy editor...</div>;
  }

  if (tenantsQuery.isError || optionsQuery.isError || policyQuery.isError) {
    const error =
      (tenantsQuery.error as Error | undefined)?.message ||
      (optionsQuery.error as Error | undefined)?.message ||
      (policyQuery.error as Error | undefined)?.message ||
      "Unable to load policy editor.";
    return <div className="panel border-rose-200 bg-rose-50 px-6 py-8 text-sm text-rose-900">{error}</div>;
  }

  const selectedTenant = tenantsQuery.data?.find((tenant) => tenant.id === selectedTenantId) ?? null;
  if (!selectedTenant || !policyQuery.data || !optionsQuery.data) {
    return <div className="panel px-6 py-8 text-sm text-slate-500">No tenant policy available.</div>;
  }

  return (
    <section className="space-y-6">
      <div className="panel flex flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Policy</div>
          <p className="mt-2 text-sm text-slate-600">
            Load a tenant policy, edit grouped controls, and save explicitly.
          </p>
        </div>

        <div>
          <label className="field-label" htmlFor="policy-tenant-select">
            Tenant
          </label>
          <select
            id="policy-tenant-select"
            className="field-input min-w-56"
            value={selectedTenantId}
            onChange={(event) => setSelectedTenantId(event.target.value)}
          >
            {tenantsQuery.data?.map((tenant) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <PolicyForm
        key={selectedTenantId}
        tenantName={selectedTenant.name}
        initialPolicy={policyQuery.data}
        options={optionsQuery.data}
        isSaving={mutation.isPending}
        onSave={async (payload) => {
          await mutation.mutateAsync(payload);
        }}
      />
    </section>
  );
}
