"use client";

import { useEffect, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getTenantPolicy, listTenants, updateTenantPolicy } from "@/lib/admin-api";
import { queryKeys } from "@/lib/query-keys";
import { Alert, AlertDescription } from "@/components/ui/alert";

type ApplyTargetProps = {
  adminKey: string;
  target: number;
};

export function ApplyTarget({ adminKey, target }: ApplyTargetProps) {
  const queryClient = useQueryClient();
  const [tenantId, setTenantId] = useState("");

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey),
    enabled: Boolean(adminKey),
  });

  useEffect(() => {
    if (!tenantId && tenantsQuery.data?.length) {
      setTenantId(tenantsQuery.data[0].id);
    }
  }, [tenantId, tenantsQuery.data]);

  const mutation = useMutation({
    mutationFn: async ({ id, value }: { id: string; value: number }) => {
      // Read the current policy first: a failed read must not turn into a partial write.
      const policy = await getTenantPolicy(adminKey, id);
      return updateTenantPolicy(adminKey, id, { ...policy, routing_quality_target: value });
    },
    onSuccess: (saved, { id }) => {
      queryClient.setQueryData(queryKeys.tenantPolicy(id), saved);
    },
  });

  const tenantName = (id: string) => tenantsQuery.data?.find((t) => t.id === id)?.name ?? id;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
        <div>
          <label htmlFor="evaluation-tenant" className="field-label">
            Tenant
          </label>
          <select
            id="evaluation-tenant"
            className="field-input"
            value={tenantId}
            onChange={(event) => {
              setTenantId(event.target.value);
              mutation.reset();
            }}
            disabled={!tenantsQuery.data?.length}
          >
            {tenantsQuery.data?.length ? null : <option value="">Sin tenants</option>}
            {tenantsQuery.data?.map((tenant) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="action-button"
          disabled={!tenantId || mutation.isPending}
          onClick={() => mutation.mutate({ id: tenantId, value: target })}
        >
          {mutation.isPending ? "Guardando…" : "Aplicar a este tenant"}
        </button>
      </div>
      <p className="text-sm text-ink-3">
        Guarda <code className="font-mono text-xs">routing_quality_target = {target.toFixed(3)}</code> en la política del
        tenant; el resto de la política no cambia.
      </p>
      {mutation.isSuccess ? (
        <div role="status" className="rounded-xl border border-ok-line bg-ok-soft px-4 py-3 text-sm text-ok">
          Guardado: routing_quality_target = {mutation.data.routing_quality_target.toFixed(3)} en{" "}
          {tenantName(mutation.variables.id)}
        </div>
      ) : null}
      {mutation.isError ? (
        <Alert variant="destructive">
          <AlertDescription>
            No se pudo aplicar: {mutation.error instanceof Error ? mutation.error.message : "error desconocido"}
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
