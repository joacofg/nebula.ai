"use client";

import { useEffect } from "react";

import Link from "next/link";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { TenantTarget } from "@/components/evaluation/use-tenant-target";
import { ErrorAlert, errorMessage } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { getTenantPolicy, updateTenantPolicy } from "@/lib/admin-api";
import { formatTarget } from "@/lib/quality-target";
import { queryKeys } from "@/lib/query-keys";

type ApplyTargetProps = {
  adminKey: string;
  tenantTarget: TenantTarget;
};

export function ApplyTarget({ adminKey, tenantTarget }: ApplyTargetProps) {
  const queryClient = useQueryClient();
  const { tenants, tenantsError, tenantId: selectedTenantId, setTenantId, currentTarget, target } = tenantTarget;
  const tenantId = selectedTenantId ?? "";

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

  // A saved (or failed) message describes the value that was applied: moving the slider retires it.
  const { reset } = mutation;
  useEffect(() => {
    reset();
  }, [target, reset]);

  const tenantName = (id: string) => tenants?.find((t) => t.id === id)?.name ?? id;

  return (
    <div className="flex flex-col gap-3">
      {tenantsError ? <ErrorAlert error={tenantsError} fallback="No se pudieron cargar los tenants." /> : null}
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
              reset();
            }}
            disabled={!tenants?.length}
          >
            {tenants?.length ? null : <option value="">Sin tenants</option>}
            {tenants?.map((tenant) => (
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
      {tenantId ? (
        <div className="flex items-baseline justify-between gap-4 text-sm">
          <p className="m-0 text-ink-2">{`Objetivo actual ${currentTarget === null ? "—" : formatTarget(currentTarget)}`}</p>
          <Link href="/playground" className="font-semibold text-ink underline underline-offset-4 hover:text-mark">
            Probar en Playground
          </Link>
        </div>
      ) : null}
      {mutation.isSuccess ? (
        <Alert variant="success" role="status">
          <AlertDescription>
            {`Objetivo ${formatTarget(mutation.data.routing_quality_target)} guardado en ${tenantName(mutation.variables.id)}.`}
          </AlertDescription>
        </Alert>
      ) : null}
      {mutation.isError ? (
        <ErrorAlert
          error={`No se pudo aplicar: ${errorMessage(mutation.error, "error desconocido")}`}
          fallback="No se pudo aplicar."
        />
      ) : null}
    </div>
  );
}
