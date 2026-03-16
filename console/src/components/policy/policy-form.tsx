"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, LoaderCircle, RotateCcw, Save } from "lucide-react";

import type { PolicyOptionsResponse, TenantPolicy } from "@/lib/admin-api";
import { ModelAllowlistInput } from "@/components/policy/model-allowlist-input";
import { PolicyAdvancedSection } from "@/components/policy/policy-advanced-section";

type PolicyFormProps = {
  tenantName: string;
  initialPolicy: TenantPolicy;
  options: PolicyOptionsResponse;
  isSaving: boolean;
  onSave: (policy: TenantPolicy) => Promise<void>;
};

type PolicyFormState = {
  routingModeDefault: TenantPolicy["routing_mode_default"];
  fallbackEnabled: boolean;
  semanticCacheEnabled: boolean;
  allowedPremiumModels: string[];
  maxPremiumCostPerRequest: string;
  softBudgetUsd: string;
  promptCaptureEnabled: boolean;
  responseCaptureEnabled: boolean;
};

function toFormState(policy: TenantPolicy): PolicyFormState {
  return {
    routingModeDefault: policy.routing_mode_default,
    fallbackEnabled: policy.fallback_enabled,
    semanticCacheEnabled: policy.semantic_cache_enabled,
    allowedPremiumModels: policy.allowed_premium_models,
    maxPremiumCostPerRequest: policy.max_premium_cost_per_request?.toString() ?? "",
    softBudgetUsd: policy.soft_budget_usd?.toString() ?? "",
    promptCaptureEnabled: policy.prompt_capture_enabled,
    responseCaptureEnabled: policy.response_capture_enabled,
  };
}

function toPolicyPayload(state: PolicyFormState): TenantPolicy {
  return {
    routing_mode_default: state.routingModeDefault,
    fallback_enabled: state.fallbackEnabled,
    semantic_cache_enabled: state.semanticCacheEnabled,
    allowed_premium_models: state.allowedPremiumModels,
    max_premium_cost_per_request:
      state.maxPremiumCostPerRequest.trim() === "" ? null : Number(state.maxPremiumCostPerRequest),
    soft_budget_usd: state.softBudgetUsd.trim() === "" ? null : Number(state.softBudgetUsd),
    prompt_capture_enabled: state.promptCaptureEnabled,
    response_capture_enabled: state.responseCaptureEnabled,
  };
}

export function PolicyForm({ tenantName, initialPolicy, options, isSaving, onSave }: PolicyFormProps) {
  const [formState, setFormState] = useState<PolicyFormState>(() => toFormState(initialPolicy));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setFormState(toFormState(initialPolicy));
    setError(null);
  }, [initialPolicy]);

  const baseline = useMemo(() => JSON.stringify(toFormState(initialPolicy)), [initialPolicy]);
  const dirty = JSON.stringify(formState) !== baseline;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const nextPolicy = toPolicyPayload(formState);
    if (nextPolicy.allowed_premium_models.length === 0) {
      setError("Select at least one premium model.");
      return;
    }

    await onSave(nextPolicy).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "Unable to update policy.");
    });
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <header className="panel px-6 py-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Policy</div>
            <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
              Policy for {tenantName}
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Structured governance controls with explicit save semantics.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {dirty ? (
              <span className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                <AlertCircle className="h-3.5 w-3.5" />
                Unsaved changes
              </span>
            ) : null}
            <button
              type="button"
              className="secondary-button gap-2"
              disabled={!dirty}
              onClick={() => setFormState(toFormState(initialPolicy))}
            >
              <RotateCcw className="h-4 w-4" />
              Reset changes
            </button>
            <button className="action-button gap-2" disabled={!dirty || isSaving} type="submit">
              {isSaving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save policy
            </button>
          </div>
        </div>
      </header>

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {error}
        </div>
      ) : null}

      <section className="panel px-6 py-5">
        <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">Routing mode</h3>
        <p className="mt-2 text-sm text-slate-500">Choose the default path for tenant traffic.</p>
        <div className="mt-4">
          <label className="field-label" htmlFor="routing-mode-default">
            Routing mode
          </label>
          <select
            id="routing-mode-default"
            className="field-input"
            value={formState.routingModeDefault}
            onChange={(event) =>
              setFormState((current) => ({
                ...current,
                routingModeDefault: event.target.value as TenantPolicy["routing_mode_default"],
              }))
            }
          >
            {options.routing_modes.map((routingMode) => (
              <option key={routingMode} value={routingMode}>
                {routingMode}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="panel px-6 py-5">
        <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">
          Execution controls
        </h3>
        <div className="mt-4 space-y-3">
          <label className="flex items-center gap-3 rounded-xl border border-border bg-slate-50 px-4 py-3 text-sm font-medium text-slate-800">
            <input
              type="checkbox"
              checked={formState.fallbackEnabled}
              onChange={(event) =>
                setFormState((current) => ({ ...current, fallbackEnabled: event.target.checked }))
              }
            />
            Fallback enabled
          </label>

          <label className="flex items-center gap-3 rounded-xl border border-border bg-slate-50 px-4 py-3 text-sm font-medium text-slate-800">
            <input
              type="checkbox"
              checked={formState.semanticCacheEnabled}
              onChange={(event) =>
                setFormState((current) => ({ ...current, semanticCacheEnabled: event.target.checked }))
              }
            />
            Semantic cache enabled
          </label>
        </div>
      </section>

      <section className="panel px-6 py-5">
        <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">
          Premium model allowlist
        </h3>
        <p className="mt-2 text-sm text-slate-500">
          Seeded from policy metadata and open to manual additions when needed.
        </p>
        <div className="mt-4">
          <ModelAllowlistInput
            knownModels={options.known_premium_models}
            value={formState.allowedPremiumModels}
            onChange={(nextValue) =>
              setFormState((current) => ({ ...current, allowedPremiumModels: nextValue }))
            }
          />
        </div>
      </section>

      <PolicyAdvancedSection
        maxPremiumCostPerRequest={formState.maxPremiumCostPerRequest}
        softBudgetUsd={formState.softBudgetUsd}
        promptCaptureEnabled={formState.promptCaptureEnabled}
        responseCaptureEnabled={formState.responseCaptureEnabled}
        onFieldChange={(field, value) =>
          setFormState((current) => ({
            ...current,
            [field]: value,
          }))
        }
        onToggleChange={(field, value) =>
          setFormState((current) => ({
            ...current,
            [field]: value,
          }))
        }
      />
    </form>
  );
}
