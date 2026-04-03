"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ArrowRight, LoaderCircle, RotateCcw, Save, Telescope } from "lucide-react";

import type {
  PolicyOptionsResponse,
  PolicySimulationChangedRequest,
  PolicySimulationResponse,
  TenantPolicy,
} from "@/lib/admin-api";
import { ModelAllowlistInput } from "@/components/policy/model-allowlist-input";
import { PolicyAdvancedSection } from "@/components/policy/policy-advanced-section";

type PolicyFormProps = {
  tenantName: string;
  initialPolicy: TenantPolicy;
  options: PolicyOptionsResponse;
  isSaving: boolean;
  isSimulating: boolean;
  simulationResult: PolicySimulationResponse | null;
  simulationError: string | null;
  onSimulate: (policy: TenantPolicy) => Promise<void>;
  onSave: (policy: TenantPolicy) => Promise<void>;
};

type PolicyFormState = {
  routingModeDefault: TenantPolicy["routing_mode_default"];
  calibratedRoutingEnabled: boolean;
  fallbackEnabled: boolean;
  semanticCacheEnabled: boolean;
  semanticCacheSimilarityThreshold: string;
  semanticCacheMaxEntryAgeHours: string;
  allowedPremiumModels: string[];
  maxPremiumCostPerRequest: string;
  hardBudgetLimitUsd: string;
  hardBudgetEnforcement: NonNullable<TenantPolicy["hard_budget_enforcement"]>;
  softBudgetUsd: string;
};

function toFormState(policy: TenantPolicy): PolicyFormState {
  return {
    routingModeDefault: policy.routing_mode_default,
    calibratedRoutingEnabled: policy.calibrated_routing_enabled,
    fallbackEnabled: policy.fallback_enabled,
    semanticCacheEnabled: policy.semantic_cache_enabled,
    semanticCacheSimilarityThreshold: policy.semantic_cache_similarity_threshold.toString(),
    semanticCacheMaxEntryAgeHours: policy.semantic_cache_max_entry_age_hours.toString(),
    allowedPremiumModels: policy.allowed_premium_models,
    maxPremiumCostPerRequest: policy.max_premium_cost_per_request?.toString() ?? "",
    hardBudgetLimitUsd: policy.hard_budget_limit_usd?.toString() ?? "",
    hardBudgetEnforcement: policy.hard_budget_enforcement ?? "downgrade",
    softBudgetUsd: policy.soft_budget_usd?.toString() ?? "",
  };
}

function toPolicyPayload(state: PolicyFormState, initialPolicy: TenantPolicy): TenantPolicy {
  const hardBudgetLimitUsd =
    state.hardBudgetLimitUsd.trim() === "" ? null : Number(state.hardBudgetLimitUsd);

  return {
    ...initialPolicy,
    routing_mode_default: state.routingModeDefault,
    calibrated_routing_enabled: state.calibratedRoutingEnabled,
    fallback_enabled: state.fallbackEnabled,
    semantic_cache_enabled: state.semanticCacheEnabled,
    semantic_cache_similarity_threshold: Number(state.semanticCacheSimilarityThreshold),
    semantic_cache_max_entry_age_hours: Number(state.semanticCacheMaxEntryAgeHours),
    allowed_premium_models: state.allowedPremiumModels,
    max_premium_cost_per_request:
      state.maxPremiumCostPerRequest.trim() === "" ? null : Number(state.maxPremiumCostPerRequest),
    hard_budget_limit_usd: hardBudgetLimitUsd,
    hard_budget_enforcement: hardBudgetLimitUsd === null ? null : state.hardBudgetEnforcement,
    soft_budget_usd: state.softBudgetUsd.trim() === "" ? null : Number(state.softBudgetUsd),
  };
}

function formatUsd(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}

function formatRouteScore(score: number | null | undefined) {
  if (score === null || score === undefined) {
    return null;
  }
  return score.toFixed(2);
}

function formatRoutingState(
  routeMode: string | null,
  calibratedRouting: boolean | null,
  degradedRouting: boolean | null,
  routeScore: number | null,
  routeReason: string | null,
) {
  if (routeMode === null && routeReason === "calibrated_routing_disabled") {
    return "rollout disabled";
  }

  const markers: string[] = [];
  if (calibratedRouting === true) {
    markers.push("calibrated");
  }
  if (degradedRouting === true) {
    markers.push("degraded");
  }

  const routeScoreLabel = formatRouteScore(routeScore);
  const detailParts = markers.join(" / ");
  const detail = [detailParts, routeScoreLabel === null ? null : `score ${routeScoreLabel}`]
    .filter((value): value is string => Boolean(value))
    .join(", ");

  if (routeMode === null) {
    return detail.length > 0 ? `unscored (${detail})` : "unscored";
  }

  return detail.length > 0 ? `${routeMode} (${detail})` : routeMode;
}

function renderChangedRequestSummary(change: PolicySimulationChangedRequest) {
  const routeChanged = change.baseline_route_target !== change.simulated_route_target;
  const statusChanged = change.baseline_terminal_status !== change.simulated_terminal_status;
  const outcomeChanged = change.baseline_policy_outcome !== change.simulated_policy_outcome;
  const costChanged = change.baseline_estimated_cost !== change.simulated_estimated_cost;

  const highlights: string[] = [];
  if (routeChanged) {
    highlights.push(`route ${change.baseline_route_target} → ${change.simulated_route_target}`);
  }
  if (statusChanged) {
    highlights.push(`status ${change.baseline_terminal_status} → ${change.simulated_terminal_status}`);
  }
  if (outcomeChanged) {
    highlights.push(
      `policy ${(change.baseline_policy_outcome ?? "none")} → ${(change.simulated_policy_outcome ?? "none")}`,
    );
  }
  if (costChanged) {
    highlights.push(`cost ${formatUsd(change.baseline_estimated_cost)} → ${formatUsd(change.simulated_estimated_cost)}`);
  }

  return highlights.join(" • ");
}

function renderChangedRequestParity(change: PolicySimulationChangedRequest) {
  return `routing parity: ${formatRoutingState(
    change.baseline_route_mode,
    change.baseline_calibrated_routing,
    change.baseline_degraded_routing,
    change.baseline_route_score,
    change.baseline_route_reason,
  )} → ${formatRoutingState(
    change.simulated_route_mode,
    change.simulated_calibrated_routing,
    change.simulated_degraded_routing,
    change.simulated_route_score,
    change.simulated_route_reason,
  )}`;
}

export function PolicyForm({
  tenantName,
  initialPolicy,
  options,
  isSaving,
  isSimulating,
  simulationResult,
  simulationError,
  onSimulate,
  onSave,
}: PolicyFormProps) {
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
  const hardBudgetConfigured = formState.hardBudgetLimitUsd.trim().length > 0;
  const cacheThresholdValue = Number(formState.semanticCacheSimilarityThreshold);
  const cacheMaxAgeValue = Number(formState.semanticCacheMaxEntryAgeHours);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const nextPolicy = toPolicyPayload(formState, initialPolicy);
    if (nextPolicy.allowed_premium_models.length === 0) {
      setError("Select at least one premium model.");
      return;
    }
    if (!Number.isFinite(cacheThresholdValue) || cacheThresholdValue < 0 || cacheThresholdValue > 1) {
      setError("Semantic cache similarity threshold must be between 0 and 1.");
      return;
    }
    if (!Number.isInteger(cacheMaxAgeValue) || cacheMaxAgeValue < 1 || cacheMaxAgeValue > 720) {
      setError("Semantic cache max entry age must be a whole number of hours between 1 and 720.");
      return;
    }

    await onSave(nextPolicy).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "Unable to update policy.");
    });
  }

  async function handleSimulate() {
    setError(null);

    const nextPolicy = toPolicyPayload(formState, initialPolicy);
    if (nextPolicy.allowed_premium_models.length === 0) {
      setError("Select at least one premium model.");
      return;
    }
    if (!Number.isFinite(cacheThresholdValue) || cacheThresholdValue < 0 || cacheThresholdValue > 1) {
      setError("Semantic cache similarity threshold must be between 0 and 1.");
      return;
    }
    if (!Number.isInteger(cacheMaxAgeValue) || cacheMaxAgeValue < 1 || cacheMaxAgeValue > 720) {
      setError("Semantic cache max entry age must be a whole number of hours between 1 and 720.");
      return;
    }

    await onSimulate(nextPolicy).catch(() => {
      // Surface the simulation mutation error via the dedicated preview panel state.
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
              Structured governance controls with explicit preview and save semantics.
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
              disabled={!dirty || isSaving || isSimulating}
              onClick={() => setFormState(toFormState(initialPolicy))}
            >
              <RotateCcw className="h-4 w-4" />
              Reset changes
            </button>
            <button
              type="button"
              className="secondary-button gap-2"
              disabled={isSaving || isSimulating}
              onClick={() => void handleSimulate()}
            >
              {isSimulating ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Telescope className="h-4 w-4" />}
              Preview impact
            </button>
            <button className="action-button gap-2" disabled={!dirty || isSaving || isSimulating} type="submit">
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

      <section className="panel px-6 py-5" aria-live="polite">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">Preview before save</h3>
            <p className="mt-2 text-sm text-slate-500">
              Replay the current draft against recent tenant traffic without persisting the policy.
            </p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            Save remains explicit
          </span>
        </div>

        {isSimulating ? (
          <div className="mt-4 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
            Simulating draft policy against recent tenant traffic...
          </div>
        ) : null}

        {simulationError ? (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            Preview failed: {simulationError}
          </div>
        ) : null}

        {!isSimulating && !simulationError && !simulationResult ? (
          <div className="mt-4 rounded-xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500">
            Run a preview to compare this draft against recent ledger-backed requests before saving.
          </div>
        ) : null}

        {simulationResult ? (
          <div className="mt-4 space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-border bg-slate-50 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Evaluated requests</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950">
                  {simulationResult.summary.evaluated_rows}
                </div>
              </div>
              <div className="rounded-xl border border-border bg-slate-50 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Changed routes</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950">
                  {simulationResult.summary.changed_routes}
                </div>
              </div>
              <div className="rounded-xl border border-border bg-slate-50 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Newly denied</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950">
                  {simulationResult.summary.newly_denied}
                </div>
              </div>
              <div className="rounded-xl border border-border bg-slate-50 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Premium cost delta</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950">
                  {formatUsd(simulationResult.summary.premium_cost_delta)}
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-slate-50 px-4 py-3 text-sm text-slate-700">
              Previewed {simulationResult.window.returned_rows} request(s) from the recent replay window. This preview did not save the policy.
            </div>

            {simulationResult.window.returned_rows === 0 ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                No recent traffic matched the replay window, so there was nothing to preview.
              </div>
            ) : simulationResult.changed_requests.length === 0 ? (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                No request outcomes changed in this replay window.
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <h4 className="font-[var(--font-fira-code)] text-base font-semibold text-slate-950">
                    Changed request sample
                  </h4>
                  <p className="mt-1 text-sm text-slate-500">
                    Compact sample of requests whose route, status, policy outcome, or projected cost changed.
                  </p>
                </div>
                <ul className="space-y-3">
                  {simulationResult.changed_requests.map((change) => (
                    <li key={change.request_id} className="rounded-xl border border-border bg-white px-4 py-3">
                      <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-slate-950">
                        <span>{change.request_id}</span>
                        <span className="text-slate-400">•</span>
                        <span>{change.requested_model}</span>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                        <span>{change.baseline_route_target}</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                        <span>{change.simulated_route_target}</span>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{renderChangedRequestSummary(change)}</p>
                      <p className="mt-1 text-xs text-slate-500">{renderChangedRequestParity(change)}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {simulationResult.approximation_notes.length > 0 ? (
              <div className="rounded-xl border border-border bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <div className="font-medium text-slate-900">Replay notes</div>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {simulationResult.approximation_notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <section className="panel px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">
              Runtime-enforced controls
            </h3>
            <p className="mt-2 text-sm text-slate-500">
              These controls change live routing behavior. Hard budget settings are cumulative tenant spend guardrails, not advisory reporting thresholds.
            </p>
          </div>
          <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
            Applies in live request evaluation
          </span>
        </div>
        <div className="mt-4 rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-950">
          When the hard cumulative budget is exhausted, Nebula either downgrades compatible auto-routed traffic to local or denies premium routing, depending on the enforcement mode below.
        </div>
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

          {runtimeEnforcedFields.has("calibrated_routing_enabled") ? (
            <div className="space-y-2 rounded-2xl border border-border bg-slate-50 px-4 py-4">
              <label className="flex items-center gap-3 text-sm font-medium text-slate-800">
                <input
                  type="checkbox"
                  checked={formState.calibratedRoutingEnabled}
                  onChange={(event) =>
                    setFormState((current) => ({
                      ...current,
                      calibratedRoutingEnabled: event.target.checked,
                    }))
                  }
                />
                Calibrated routing enabled
              </label>
              <p className="text-sm text-slate-500">
                Tenant-scoped rollout valve for token-complexity auto routing. Turning this off keeps explicit model overrides and policy-forced routing intact while forcing auto-routed requests onto the local path.
              </p>
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
            <div className="space-y-4 rounded-2xl border border-border bg-slate-50 px-4 py-4">
              <label className="flex items-center gap-3 text-sm font-medium text-slate-800">
                <input
                  type="checkbox"
                  checked={formState.semanticCacheEnabled}
                  onChange={(event) =>
                    setFormState((current) => ({ ...current, semanticCacheEnabled: event.target.checked }))
                  }
                />
                Semantic cache enabled
              </label>
              <p className="text-sm text-slate-500">
                Runtime-enforced cache controls stay in this policy editor. Adjust them deliberately, preview the
                draft against recent ledger-backed traffic, and save explicitly when the evidence supports the change.
              </p>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="field-label" htmlFor="semantic-cache-similarity-threshold">
                    Semantic cache similarity threshold
                  </label>
                  <input
                    id="semantic-cache-similarity-threshold"
                    className="field-input"
                    inputMode="decimal"
                    value={formState.semanticCacheSimilarityThreshold}
                    onChange={(event) =>
                      setFormState((current) => ({
                        ...current,
                        semanticCacheSimilarityThreshold: event.target.value,
                      }))
                    }
                  />
                  <p className="mt-2 text-sm text-slate-500">
                    Higher values require a closer semantic match before Nebula reuses a cached response.
                  </p>
                </div>
                <div>
                  <label className="field-label" htmlFor="semantic-cache-max-entry-age-hours">
                    Semantic cache max entry age hours
                  </label>
                  <input
                    id="semantic-cache-max-entry-age-hours"
                    className="field-input"
                    inputMode="numeric"
                    value={formState.semanticCacheMaxEntryAgeHours}
                    onChange={(event) =>
                      setFormState((current) => ({
                        ...current,
                        semanticCacheMaxEntryAgeHours: event.target.value,
                      }))
                    }
                  />
                  <p className="mt-2 text-sm text-slate-500">
                    Lower values age out cached entries sooner when recent traffic suggests stale reuse risk.
                  </p>
                </div>
              </div>
            </div>
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

          {runtimeEnforcedFields.has("hard_budget_limit_usd") ? (
            <div>
              <label className="field-label" htmlFor="hard-budget-limit-usd">
                Hard cumulative budget limit USD
              </label>
              <input
                id="hard-budget-limit-usd"
                className="field-input"
                inputMode="decimal"
                value={formState.hardBudgetLimitUsd}
                onChange={(event) =>
                  setFormState((current) => ({
                    ...current,
                    hardBudgetLimitUsd: event.target.value,
                  }))
                }
              />
              <p className="mt-2 text-sm text-slate-500">
                Tracks cumulative premium spend for the tenant. Leave blank to disable the hard budget guardrail.
              </p>
            </div>
          ) : null}

          {runtimeEnforcedFields.has("hard_budget_enforcement") ? (
            <div>
              <label className="field-label" htmlFor="hard-budget-enforcement">
                Hard budget enforcement
              </label>
              <select
                id="hard-budget-enforcement"
                className="field-input"
                value={formState.hardBudgetEnforcement}
                disabled={!hardBudgetConfigured}
                onChange={(event) =>
                  setFormState((current) => ({
                    ...current,
                    hardBudgetEnforcement: event.target.value as NonNullable<
                      TenantPolicy["hard_budget_enforcement"]
                    >,
                  }))
                }
              >
                <option value="downgrade">Downgrade compatible auto-routed traffic to local</option>
                <option value="deny">Deny premium traffic once the limit is exhausted</option>
              </select>
              <p className="mt-2 text-sm text-slate-500">
                {hardBudgetConfigured
                  ? "Applies when cumulative premium spend reaches the hard budget limit. Explicit premium requests still deny when downgrade is not allowed."
                  : "Set a hard cumulative budget limit first to activate this enforcement choice."}
              </p>
            </div>
          ) : null}
        </div>
      </section>

      {softSignalFields.has("soft_budget_usd") ? (
        <section className="panel px-6 py-5">
          <h3 className="font-[var(--font-fira-code)] text-lg font-semibold text-slate-950">Soft budget advisory</h3>
          <p className="mt-2 text-sm text-slate-500">
            Advisory only. Exceeding this threshold adds operator-visible policy outcome metadata, but it does not block, downgrade, or deny routing.
          </p>
          <div className="mt-4 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-950">
            Use this to flag spend pressure for operators. Use the hard budget controls above when tenant traffic must change at runtime.
          </div>
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

