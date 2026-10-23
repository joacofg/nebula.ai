"use client";

import Link from "next/link";

import type { TenantTarget } from "@/components/evaluation/use-tenant-target";
import { ErrorAlert, errorMessage } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { formatTarget } from "@/lib/quality-target";

type ApplyTargetProps = {
  tenantTarget: TenantTarget;
};

export function ApplyTarget({ tenantTarget }: ApplyTargetProps) {
  const {
    tenants,
    tenantsError,
    policyError,
    tenantId: selectedTenantId,
    setTenantId,
    currentTarget,
    target,
    saving,
    settling,
    apply,
  } = tenantTarget;
  const tenantId = selectedTenantId ?? "";

  const tenantName = (id: string) => tenants?.find((t) => t.id === id)?.name ?? id;

  return (
    <div className="flex flex-col gap-3">
      {tenantsError ? <ErrorAlert error={tenantsError} fallback="No se pudieron cargar los tenants." /> : null}
      {policyError ? (
        <ErrorAlert error={policyError} fallback="No se pudo cargar el objetivo actual del tenant." />
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
            onChange={(event) => setTenantId(event.target.value)}
            disabled={!tenants?.length || saving}
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
          disabled={!tenantId || saving || settling}
          onClick={() => apply.mutate({ id: tenantId, value: target })}
        >
          {saving ? "Guardando…" : "Aplicar al tenant"}
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
      {apply.isSuccess ? (
        <Alert variant="success" role="status">
          <AlertDescription>
            {`Objetivo ${formatTarget(apply.data.routing_quality_target)} guardado en ${tenantName(apply.variables.id)}.`}
          </AlertDescription>
        </Alert>
      ) : null}
      {apply.isError ? (
        <ErrorAlert
          error={`No se pudo aplicar: ${errorMessage(apply.error, "error desconocido")}`}
          fallback="No se pudo aplicar."
        />
      ) : null}
    </div>
  );
}
