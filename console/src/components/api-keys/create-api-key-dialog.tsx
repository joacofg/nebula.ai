"use client";

import { useEffect, useMemo, useState } from "react";
import { LoaderCircle, Plus } from "lucide-react";

import type { ApiKeyCreateInput, TenantRecord } from "@/lib/admin-api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";


type CreateApiKeyDialogProps = {
  open: boolean;
  tenants: TenantRecord[];
  selectedTenantId: string | null;
  isSaving: boolean;
  onClose: () => void;
  onSubmit: (payload: ApiKeyCreateInput) => Promise<void>;
};

export function CreateApiKeyDialog({
  open,
  tenants,
  selectedTenantId,
  isSaving,
  onClose,
  onSubmit,
}: CreateApiKeyDialogProps) {
  const initialTenant = useMemo(
    () => selectedTenantId ?? tenants[0]?.id ?? null,
    [selectedTenantId, tenants],
  );
  const [name, setName] = useState("");
  const [tenantId, setTenantId] = useState<string | null>(initialTenant);
  const [allowedTenantIds, setAllowedTenantIds] = useState<string[]>(initialTenant ? [initialTenant] : []);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    const nextTenant = selectedTenantId ?? tenants[0]?.id ?? null;
    setTenantId(nextTenant);
    setAllowedTenantIds(nextTenant ? [nextTenant] : []);
    setName("");
    setError(null);
  }, [open, selectedTenantId, tenants]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Falta el nombre.");
      return;
    }
    if (allowedTenantIds.length === 0) {
      setError("Elegir al menos un tenant permitido.");
      return;
    }

    await onSubmit({
      name: name.trim(),
      tenant_id: tenantId,
      allowed_tenant_ids: allowedTenantIds,
    }).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "No se pudo crear la clave.");
    });
  }

  function toggleAllowedTenant(nextTenantId: string) {
    setAllowedTenantIds((current) =>
      current.includes(nextTenantId)
        ? current.filter((tenant) => tenant !== nextTenantId)
        : [...current, nextTenantId],
    );
  }

  return (
    <Dialog open={open} onOpenChange={(next) => (next ? null : onClose())}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold text-ink">Nueva clave de API</DialogTitle>
          <DialogDescription className="text-sm text-ink-3">La clave se muestra una sola vez al crearla.</DialogDescription>
        </DialogHeader>

        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <div>
            <label className="field-label" htmlFor="api-key-name">
              Nombre
            </label>
            <input id="api-key-name" className="field-input" value={name} onChange={(event) => setName(event.target.value)} />
          </div>

          <div>
            <label className="field-label" htmlFor="tenant-id">
              Tenant por defecto
            </label>
            <select
              id="tenant-id"
              className="field-input"
              value={tenantId ?? ""}
              onChange={(event) => setTenantId(event.target.value || null)}
            >
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </option>
              ))}
            </select>
          </div>

          <fieldset className="m-0 border-0 p-0">
            <legend className="field-label">Tenants permitidos</legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {tenants.map((tenant) => (
                <label key={tenant.id} className="flex items-center gap-2.5 text-[15px] text-ink">
                  <input
                    type="checkbox"
                    className="size-4 accent-ink"
                    checked={allowedTenantIds.includes(tenant.id)}
                    onChange={() => toggleAllowedTenant(tenant.id)}
                  />
                  <span>{tenant.name}</span>
                </label>
              ))}
            </div>
            <p className="mt-1.5 text-[13px] text-ink-3">
              Con más de uno y sin tenant por defecto, los pedidos envían X-Nebula-Tenant-ID.
            </p>
          </fieldset>

          <Button type="submit" size="lg" disabled={isSaving} className="w-full">
            {isSaving ? <LoaderCircle aria-hidden className="size-4 animate-spin" /> : <Plus aria-hidden className="size-4" />}
            Crear clave
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
