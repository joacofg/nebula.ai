"use client";

import { useEffect, useMemo, useState } from "react";
import { LoaderCircle, PanelRightOpen } from "lucide-react";

import type { TenantInput, TenantRecord } from "@/lib/admin-api";

const TENANT_UPDATE_HINT = "/api/admin/tenants/";

type TenantEditorDrawerProps = {
  mode: "create" | "edit";
  tenant: TenantRecord | null;
  isSaving: boolean;
  onClose: () => void;
  onSubmit: (payload: TenantInput) => Promise<void>;
};

type FormState = {
  id: string;
  name: string;
  description: string;
  active: boolean;
  metadata: string;
};

const EMPTY_FORM: FormState = {
  id: "",
  name: "",
  description: "",
  active: true,
  metadata: "{}",
};

function toFormState(tenant: TenantRecord | null): FormState {
  if (!tenant) {
    return EMPTY_FORM;
  }
  return {
    id: tenant.id,
    name: tenant.name,
    description: tenant.description ?? "",
    active: tenant.active,
    metadata: JSON.stringify(tenant.metadata ?? {}, null, 2),
  };
}

export function TenantEditorDrawer({
  mode,
  tenant,
  isSaving,
  onClose,
  onSubmit,
}: TenantEditorDrawerProps) {
  const [formState, setFormState] = useState<FormState>(toFormState(tenant));
  const [error, setError] = useState<string | null>(null);
  const isEditMode = mode === "edit";

  useEffect(() => {
    setFormState(toFormState(tenant));
    setError(null);
  }, [mode, tenant]);

  const heading = useMemo(
    () => (isEditMode ? `Edit ${tenant?.name ?? "tenant"}` : "Create tenant"),
    [isEditMode, tenant?.name],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    let metadata: Record<string, unknown> = {};
    try {
      metadata = JSON.parse(formState.metadata || "{}") as Record<string, unknown>;
    } catch {
      setError("metadata must be valid JSON.");
      return;
    }

    if (!formState.id.trim() || !formState.name.trim()) {
      setError("id and name are required.");
      return;
    }

    await onSubmit({
      id: formState.id.trim(),
      name: formState.name.trim(),
      description: formState.description.trim(),
      active: formState.active,
      metadata,
    }).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "Unable to save tenant.");
    });
  }

  return (
    <aside className="panel h-full min-h-[32rem] px-5 py-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
            {isEditMode ? "Tenant detail" : "New tenant"}
          </div>
          <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">{heading}</h3>
          <p className="mt-2 text-sm text-slate-500">
            {isEditMode
              ? `Updates flow through ${TENANT_UPDATE_HINT}${tenant?.id ?? "{tenant_id}"}.`
              : "Create a workspace with governance metadata and an explicit active state."}
          </p>
        </div>
        <button
          type="button"
          className="secondary-button gap-2 px-3 py-2"
          onClick={onClose}
        >
          <PanelRightOpen className="h-4 w-4" />
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
          <label className="field-label" htmlFor="tenant-id">
            id
          </label>
          <input
            id="tenant-id"
            className="field-input font-[var(--font-fira-code)] text-xs"
            value={formState.id}
            readOnly={isEditMode}
            onChange={(event) => setFormState((current) => ({ ...current, id: event.target.value }))}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="tenant-name">
            name
          </label>
          <input
            id="tenant-name"
            className="field-input"
            value={formState.name}
            onChange={(event) => setFormState((current) => ({ ...current, name: event.target.value }))}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="tenant-description">
            Description
          </label>
          <textarea
            id="tenant-description"
            className="field-input min-h-24 resize-y"
            value={formState.description}
            onChange={(event) =>
              setFormState((current) => ({ ...current, description: event.target.value }))
            }
          />
        </div>

        <label className="flex items-center gap-3 rounded-xl border border-border bg-slate-50 px-4 py-3 text-sm font-medium text-slate-800">
          <input
            type="checkbox"
            checked={formState.active}
            onChange={(event) => setFormState((current) => ({ ...current, active: event.target.checked }))}
          />
          active
        </label>

        <div>
          <label className="field-label" htmlFor="tenant-metadata">
            metadata
          </label>
          <textarea
            id="tenant-metadata"
            className="field-input min-h-40 resize-y font-[var(--font-fira-code)] text-xs"
            value={formState.metadata}
            onChange={(event) => setFormState((current) => ({ ...current, metadata: event.target.value }))}
          />
        </div>

        <button className="action-button w-full gap-2" disabled={isSaving} type="submit">
          {isSaving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
          {isEditMode ? "Save tenant" : "Create tenant"}
        </button>
      </form>
    </aside>
  );
}
