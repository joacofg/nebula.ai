"use client";

import { useState } from "react";
import { LoaderCircle, PanelRightOpen } from "lucide-react";

import type { DeploymentCreateInput, DeploymentEnvironment } from "@/lib/admin-api";

type CreateDeploymentSlotDrawerProps = {
  isSaving: boolean;
  onClose: () => void;
  onSubmit: (payload: DeploymentCreateInput) => Promise<void>;
};

type FormState = {
  display_name: string;
  environment: DeploymentEnvironment;
};

const EMPTY_FORM: FormState = {
  display_name: "",
  environment: "production",
};

export function CreateDeploymentSlotDrawer({
  isSaving,
  onClose,
  onSubmit,
}: CreateDeploymentSlotDrawerProps) {
  const [formState, setFormState] = useState<FormState>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!formState.display_name.trim()) {
      setError("Display name is required.");
      return;
    }

    await onSubmit({
      display_name: formState.display_name.trim(),
      environment: formState.environment,
    }).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "Unable to create deployment slot.");
    });
  }

  return (
    <aside className="panel h-full min-h-[32rem] px-5 py-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
            New deployment
          </div>
          <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
            Create deployment slot
          </h3>
          <p className="mt-2 text-sm text-slate-500">
            Reserve a named slot in the hosted inventory. You will receive a one-time enrollment
            token to complete the link.
          </p>
        </div>
        <button type="button" className="secondary-button gap-2 px-3 py-2" onClick={onClose}>
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
          <label className="field-label" htmlFor="deployment-name">
            Display name
          </label>
          <input
            id="deployment-name"
            className="field-input"
            placeholder="e.g. prod-gateway-us-east"
            value={formState.display_name}
            onChange={(event) =>
              setFormState((current) => ({ ...current, display_name: event.target.value }))
            }
          />
        </div>

        <div>
          <label className="field-label" htmlFor="deployment-environment">
            Environment
          </label>
          <select
            id="deployment-environment"
            className="field-input"
            value={formState.environment}
            onChange={(event) =>
              setFormState((current) => ({
                ...current,
                environment: event.target.value as DeploymentEnvironment,
              }))
            }
          >
            <option value="production">Production</option>
            <option value="staging">Staging</option>
            <option value="development">Development</option>
          </select>
          <p className="mt-1 text-xs text-slate-500">
            Linking is outbound-only. The hosted plane receives metadata only — no prompts,
            responses, or provider credentials.
          </p>
        </div>

        <button className="action-button w-full gap-2" disabled={isSaving} type="submit">
          {isSaving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
          Create deployment slot
        </button>
      </form>
    </aside>
  );
}
