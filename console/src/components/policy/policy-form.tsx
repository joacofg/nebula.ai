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
};

function toFormState(policy: TenantPolicy): PolicyFormState {
  return {
    routingModeDefault: policy.routing_mode_default,
    fallbackEnabled: policy.fallback_enabled,
    semanticCacheEnabled: policy.semantic_cache_enabled,
    allowedPremiumModels: policy.allowed_premium_models,
    maxPremiumCostPerRequest: policy.max_premium_cost_per_request?.toString() ?? "",
    softBudgetUsd: policy.soft_budget_usd?.toString() ?? "",
  };
}

function toPolicyPayload(state: PolicyFormState, initialPolicy: TenantPolicy): TenantPolicy {
  return {
    ...initialPolicy,
    routing_mode_default: state.routingModeDefault,
    fallback_enabled: state.fallbackEnabled,
    semantic_cache_enabled: state.semanticCacheEnabled,
    allowed_premium_models: state.allowedPremiumModels,
    max_premium_cost_per_request:
      state.maxPremiumCostPerRequest.trim() === "" ? null : Number(state.maxPremiumCostPerRequest),
    soft_budget_usd: state.softBudgetUsd.trim() === "" ? null : Number(state.softBudgetUsd),
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
  const runtimeEnforcedFields = useMemo(
    () => new Set(options.runtime_enforced_fields),
    [options.runtime_enforced_fields],
  );
  const softSignalFields = useMemo(() => new Set(options.soft_signal_fields), [options.soft_signal_fields]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const nextPolicy = toPolicyPayload(formState, initialPolicy);
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
        <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">
          Runtime-enforced controls
        </h3>
        <p className="mt-2 text-sm text-slate-500">
          These controls map directly to the backend runtime enforcement contract for Phase 4.
        </p>
        <div className="mt-4 space-y-5">
          {runtimeEnforcedFields.has("routing_mode_default") ? (
            <div>
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
          ) : null}

          {runtimeEnforcedFields.has("fallback_enabled") ? (
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
          ) : null}

          {runtimeEnforcedFields.has("semantic_cache_enabled") ? (
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
          ) : null}

          {runtimeEnforcedFields.has("allowed_premium_models") ? (
            <div>
              <h4 className="font-[var(--font-fira-code)] text-base font-semibold text-slate-950">
                Premium model allowlist
              </h4>
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
            </div>
          ) : null}

          {runtimeEnforcedFields.has("max_premium_cost_per_request") ? (
            <div>
              <label className="field-label" htmlFor="max-premium-cost">
                Max premium cost per request
              </label>
              <input
                id="max-premium-cost"
                className="field-input"
                inputMode="decimal"
                value={formState.maxPremiumCostPerRequest}
                onChange={(event) =>
                  setFormState((current) => ({
                    ...current,
                    maxPremiumCostPerRequest: event.target.value,
                  }))
                }
              />
            </div>
          ) : null}
        </div>
      </section>

      {softSignalFields.has("soft_budget_usd") ? (
        <section className="panel px-6 py-5">
          <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">Soft budget signal</h3>
          <p className="mt-2 text-sm text-slate-500">
            Soft budget signal only. Adds policy outcome metadata when exceeded but does not block routing in Phase 4.
          </p>
          <div className="mt-4">
            <label className="field-label" htmlFor="soft-budget-usd">
              Soft budget USD
            </label>
            <input
              id="soft-budget-usd"
              className="field-input"
              inputMode="decimal"
              value={formState.softBudgetUsd}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  softBudgetUsd: event.target.value,
                }))
              }
            />
          </div>
        </section>
      ) : null}

      <PolicyAdvancedSection />
    </form>
  );
}
