"use client";

import { useEffect, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getTenantPolicy, listTenants, updateTenantPolicy } from "@/lib/admin-api";
import { queryKeys } from "@/lib/query-keys";
import { ErrorAlert } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

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
    <div className="flex flex-col gap-3">
      {tenantsQuery.isError ? (
        <ErrorAlert error={tenantsQuery.error} fallback="No se pudieron cargar los tenants." />
      ) : null}
      <div className="flex items-end gap-2">
        <div className="min-w-0 flex-1">
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
        <Button
          type="button"
          disabled={!tenantId || mutation.isPending}
          onClick={() => mutation.mutate({ id: tenantId, value: target })}
        >
          {mutation.isPending ? "Guardando…" : "Aplicar al tenant"}
        </Button>
      </div>
      {mutation.isSuccess ? (
        <Alert variant="success" role="status">
          <AlertDescription>
            {`Objetivo ${mutation.data.routing_quality_target.toFixed(3)} guardado en ${tenantName(mutation.variables.id)}.`}
          </AlertDescription>
        </Alert>
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
