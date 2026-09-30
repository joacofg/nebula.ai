"use client";

import { useEffect, useMemo, useState } from "react";
import { LoaderCircle, Plus } from "lucide-react";

import type { ApiKeyCreateInput, TenantRecord } from "@/lib/admin-api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const API_KEYS_ENDPOINT = "/api/admin/api-keys";

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
      setError("name is required.");
      return;
    }
    if (allowedTenantIds.length === 0) {
      setError("allowed_tenant_ids must contain at least one tenant.");
      return;
    }

    await onSubmit({
      name: name.trim(),
      tenant_id: tenantId,
      allowed_tenant_ids: allowedTenantIds,
    }).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "Unable to create API key.");
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
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">New API key</div>
          <DialogTitle className="text-xl font-semibold text-ink">Issue client credentials with tenant scope</DialogTitle>
          <DialogDescription className="text-sm text-ink-4">
            Creates a client API key through <span className="font-mono">{API_KEYS_ENDPOINT}</span>.
            {" "}Use <span className="font-mono">allowed_tenant_ids</span> to define every tenant the
            key may access.
          </DialogDescription>
          <p className="text-sm text-ink-4">
            Nebula resolves requests by honoring an explicit <span className="font-mono">X-Nebula-Tenant-ID</span>
            when it matches an allowed tenant; otherwise it falls back to <span className="font-mono">tenant_id</span>,
            then to the only allowed tenant. If you authorize multiple tenants without a default
            <span className="font-mono"> tenant_id</span>, public callers must send the tenant header.
          </p>
        </DialogHeader>

        <form className="mt-2 space-y-4" onSubmit={handleSubmit}>
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <div>
            <label className="field-label" htmlFor="api-key-name">
              name
            </label>
            <input
              id="api-key-name"
              className="field-input"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>

          <div>
            <label className="field-label" htmlFor="tenant-id">
              tenant_id
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
            <p className="mt-2 text-xs leading-5 text-ink-4">
              Default tenant for callers that omit <span className="font-mono">X-Nebula-Tenant-ID</span>.
              Leave the key single-tenant or send the header when requests should resolve elsewhere.
            </p>
          </div>

          <div>
            <span className="field-label">allowed_tenant_ids</span>
            <p className="mt-2 text-xs leading-5 text-ink-4">
              Every tenant this key may access. A single allowed tenant is inferred automatically; multiple
              allowed tenants are an intentional multi-tenant authorization boundary.
            </p>
            <div className="mt-3 grid gap-2 rounded-2xl border border-line bg-canvas p-3 sm:grid-cols-2">
              {tenants.map((tenant) => (
                <label key={tenant.id} className="flex items-center gap-3 rounded-xl bg-surface px-3 py-2 text-sm text-ink-2">
                  <input
                    type="checkbox"
                    checked={allowedTenantIds.includes(tenant.id)}
                    onChange={() => toggleAllowedTenant(tenant.id)}
                  />
                  <span>{tenant.name}</span>
                </label>
              ))}
            </div>
          </div>

          <button className="action-button w-full gap-2" disabled={isSaving} type="submit">
            {isSaving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Create API key
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
