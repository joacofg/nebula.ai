"use client";

import { useEffect, useMemo, useState } from "react";
import { LoaderCircle, Plus } from "lucide-react";

import type { ApiKeyCreateInput, TenantRecord } from "@/lib/admin-api";

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

  if (!open) {
    return null;
  }

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
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/35 px-4 py-6 backdrop-blur-sm">
      <div className="panel w-full max-w-2xl px-6 py-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">New API key</div>
            <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
              Issue a tenant-scoped key
            </h3>
            <p className="mt-2 text-sm text-slate-500">
              Creates a key through <span className="font-[var(--font-fira-code)]">{API_KEYS_ENDPOINT}</span> with
              explicit <span className="font-[var(--font-fira-code)]">allowed_tenant_ids</span>.
            </p>
          </div>
          <button type="button" className="secondary-button px-3 py-2" onClick={onClose}>
            Close
          </button>
        </div>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          {error ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
              {error}
            </div>
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
          </div>

          <div>
            <span className="field-label">allowed_tenant_ids</span>
            <div className="grid gap-2 rounded-2xl border border-border bg-slate-50 p-3 sm:grid-cols-2">
              {tenants.map((tenant) => (
                <label key={tenant.id} className="flex items-center gap-3 rounded-xl bg-white px-3 py-2 text-sm text-slate-800">
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
      </div>
    </div>
  );
}
