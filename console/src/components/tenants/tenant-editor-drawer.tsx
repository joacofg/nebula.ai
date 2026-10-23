"use client";

import { useEffect, useRef, useState } from "react";
import { LoaderCircle, X } from "lucide-react";

import type { TenantInput, TenantRecord } from "@/lib/admin-api";
import { ErrorAlert } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type TenantEditorDrawerProps = (
  | { mode: "create"; tenant: null }
  | { mode: "edit"; tenant: TenantRecord }
) & {
  isSaving: boolean;
  /** What just happened to the tenant, shown as a status line. */
  notice?: string | null;
  /** Each increase moves focus to the first field; 0 leaves it alone. */
  focusRequest?: number;
  onClose: () => void;
  /** Any change to a field: the page takes its notice away. */
  onEdit?: () => void;
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
  notice = null,
  focusRequest = 0,
  onClose,
  onEdit,
  onSubmit,
}: TenantEditorDrawerProps) {
  const [formState, setFormState] = useState<FormState>(toFormState(tenant));
  const [error, setError] = useState<string | null>(null);
  const firstFieldRef = useRef<HTMLInputElement>(null);
  const isEditMode = mode === "edit";

  const update = (patch: Partial<FormState>) => {
    setFormState((current) => ({ ...current, ...patch }));
    onEdit?.();
  };

  // The form follows which tenant is open, not each fresh copy of its record: a background refetch
  // must not discard what the operator is typing.
  const openKey = `${mode}:${tenant?.id ?? ""}`;
  const [shownKey, setShownKey] = useState(openKey);
  if (shownKey !== openKey) {
    setShownKey(openKey);
    setFormState(toFormState(tenant));
    setError(null);
  }

  useEffect(() => {
    if (focusRequest > 0) {
      firstFieldRef.current?.focus();
    }
  }, [focusRequest]);

  const heading = tenant ? `Editar ${tenant.name}` : "Nuevo tenant";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    let metadata: Record<string, unknown> = {};
    try {
      metadata = JSON.parse(formState.metadata || "{}") as Record<string, unknown>;
    } catch {
      setError("Los metadatos tienen que ser JSON válido.");
      return;
    }

    if (!formState.id.trim() || !formState.name.trim()) {
      setError("Faltan el id o el nombre.");
      return;
    }

    await onSubmit({
      id: formState.id.trim(),
      name: formState.name.trim(),
      description: formState.description.trim(),
      active: formState.active,
      metadata,
    }).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "No se pudo guardar el tenant.");
    });
  }

  return (
    <aside className="flex flex-col gap-5 px-6 py-6" aria-labelledby="tenant-editor-heading">
      <div className="flex items-start justify-between gap-3">
        <h2 id="tenant-editor-heading" className="m-0 text-lg font-semibold text-ink">
          {heading}
        </h2>
        <Button type="button" variant="ghost" size="sm" onClick={onClose}>
          <X aria-hidden className="size-4" />
          Cerrar
        </Button>
      </div>

      <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
        {notice ? (
          <Alert variant="success" role="status">
            <AlertDescription>{notice}</AlertDescription>
          </Alert>
        ) : null}
        {error ? <ErrorAlert error={error} fallback="No se pudo guardar el tenant." /> : null}

        <div>
          <label className="field-label" htmlFor="tenant-id">
            Id
          </label>
          <input
            id="tenant-id"
            ref={firstFieldRef}
            className="field-input font-mono text-[13px] read-only:bg-canvas read-only:text-ink-2"
            value={formState.id}
            readOnly={isEditMode}
            onChange={(event) => update({ id: event.target.value })}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="tenant-name">
            Nombre
          </label>
          <input
            id="tenant-name"
            className="field-input"
            value={formState.name}
            onChange={(event) => update({ name: event.target.value })}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="tenant-description">
            Descripción
          </label>
          <textarea
            id="tenant-description"
            className="field-input min-h-20 resize-y"
            value={formState.description}
            onChange={(event) => update({ description: event.target.value })}
          />
        </div>

        <label className="flex items-center gap-2.5 text-[15px] font-medium text-ink">
          <input
            type="checkbox"
            className="size-4 accent-ink"
            checked={formState.active}
            onChange={(event) => update({ active: event.target.checked })}
          />
          Activo
        </label>

        <div>
          <label className="field-label" htmlFor="tenant-metadata">
            Metadatos
          </label>
          <textarea
            id="tenant-metadata"
            className="field-input min-h-32 resize-y font-mono text-[13px]"
            value={formState.metadata}
            onChange={(event) => update({ metadata: event.target.value })}
          />
          <p className="mt-1.5 text-[13px] text-ink-3">Notas del operador; Nebula no valida su esquema.</p>
        </div>

        <Button type="submit" size="lg" disabled={isSaving} className="w-full">
          {isSaving ? <LoaderCircle aria-hidden className="size-4 animate-spin" /> : null}
          {isEditMode ? "Guardar tenant" : "Crear tenant"}
        </Button>
      </form>
    </aside>
  );
}
