"use client";

import { useEffect, useId, useMemo, useState, type ReactNode } from "react";
import { AlertCircle, ArrowRight, LoaderCircle, RotateCcw, Save, Telescope } from "lucide-react";

import type {
  PolicyOptionsResponse,
  PolicySimulationChangedRequest,
  PolicySimulationOutcomeCounts,
  PolicySimulationResponse,
  TenantPolicy,
  TierCounts,
} from "@/lib/admin-api";
import { ModelAllowlistInput } from "@/components/policy/model-allowlist-input";
import {
  numberText,
  parsePolicyNumber,
  policyFormChanged,
  validatePolicyForm,
  type PolicyFormErrors,
  type PolicyFormField,
  type PolicyFormState,
  type TenantPolicyPayload,
} from "@/components/policy/policy-validation";
import {
  approximationNoteLabel,
  reasonLabel,
  routeLabel,
  routingModeLabel,
  scoreModeLabel,
  statusLabel,
} from "@/components/system/labels";
import { Readout, type ReadoutItem } from "@/components/system/readout";
import { ErrorAlert, LoadingRows } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { formatUsd } from "@/lib/format";
import { TARGET_MAX, TARGET_MIN, formatTarget } from "@/lib/quality-target";
import { TIERS } from "@/lib/router-replay";

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

// The label of every field, in the order the form shows them: the fields, and the panel that
// names the ones to fix, read from here.
const FIELD_LABELS: Record<PolicyFormField, string> = {
  routingQualityTarget: "Objetivo de calidad",
  routingModeDefault: "Modo de ruteo",
  calibratedRoutingEnabled: "Ruteo automático por nivel",
  fallbackEnabled: "Fallback a premium si falla el local",
  rateLimitRequestsPerMinute: "Límite de pedidos por minuto",
  maxPremiumCostPerRequest: "Costo premium máximo por pedido (USD)",
  hardBudgetLimitUsd: "Presupuesto duro acumulado (USD)",
  hardBudgetEnforcement: "Al agotarse el presupuesto",
  softBudgetUsd: "Presupuesto blando (USD)",
  semanticCacheEnabled: "Caché semántico activado",
  semanticCacheSimilarityThreshold: "Umbral de similitud",
  semanticCacheMaxEntryAgeHours: "Antigüedad máxima (h)",
  allowedPremiumModels: "Modelos premium permitidos",
  evidenceRetentionWindow: "Retención de evidencia",
  metadataMinimizationLevel: "Minimización de metadatos",
};

// The runtime field that shows each form field: one the gateway does not enforce is not shown, so it
// is neither checked nor written. `soft` marks a field the gateway only reports as a signal.
const FIELD_GATES: Record<PolicyFormField, { field: string; soft?: true }> = {
  routingQualityTarget: { field: "routing_quality_target" },
  routingModeDefault: { field: "routing_mode_default" },
  calibratedRoutingEnabled: { field: "calibrated_routing_enabled" },
  fallbackEnabled: { field: "fallback_enabled" },
  rateLimitRequestsPerMinute: { field: "rate_limit_requests_per_minute" },
  maxPremiumCostPerRequest: { field: "max_premium_cost_per_request" },
  hardBudgetLimitUsd: { field: "hard_budget_limit_usd" },
  hardBudgetEnforcement: { field: "hard_budget_enforcement" },
  softBudgetUsd: { field: "soft_budget_usd", soft: true },
  semanticCacheEnabled: { field: "semantic_cache_enabled" },
  semanticCacheSimilarityThreshold: { field: "semantic_cache_enabled" },
  semanticCacheMaxEntryAgeHours: { field: "semantic_cache_enabled" },
  allowedPremiumModels: { field: "allowed_premium_models" },
  evidenceRetentionWindow: { field: "evidence_retention_window" },
  metadataMinimizationLevel: { field: "metadata_minimization_level" },
};

// Gateway default (TenantPolicy.routing_quality_target) for policies saved before the field existed.
const DEFAULT_ROUTING_QUALITY_TARGET = 0.95;

function toFormState(policy: TenantPolicy): PolicyFormState {
  return {
    routingModeDefault: policy.routing_mode_default,
    calibratedRoutingEnabled: policy.calibrated_routing_enabled,
    fallbackEnabled: policy.fallback_enabled,
    semanticCacheEnabled: policy.semantic_cache_enabled,
    semanticCacheSimilarityThreshold: numberText(policy.semantic_cache_similarity_threshold),
    semanticCacheMaxEntryAgeHours: numberText(policy.semantic_cache_max_entry_age_hours),
    allowedPremiumModels: policy.allowed_premium_models,
    maxPremiumCostPerRequest: numberText(policy.max_premium_cost_per_request),
    hardBudgetLimitUsd: numberText(policy.hard_budget_limit_usd),
    hardBudgetEnforcement: policy.hard_budget_enforcement ?? "downgrade",
    softBudgetUsd: numberText(policy.soft_budget_usd),
    evidenceRetentionWindow: policy.evidence_retention_window,
    metadataMinimizationLevel: policy.metadata_minimization_level,
    // A stored target outside the console's range shows as it is; saving it asks for a new one.
    routingQualityTarget: formatTarget(policy.routing_quality_target ?? DEFAULT_ROUTING_QUALITY_TARGET),
    rateLimitRequestsPerMinute: numberText(policy.rate_limit_requests_per_minute),
  };
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
    return reasonLabel(routeReason);
  }

  const modeLabel = routeMode === null ? null : scoreModeLabel(routeMode);
  const markers: string[] = [];
  if (calibratedRouting === true) {
    markers.push(scoreModeLabel("calibrated"));
  }
  if (degradedRouting === true) {
    markers.push(scoreModeLabel("degraded"));
  }

  const routeScoreLabel = formatRouteScore(routeScore);
  // A marker that repeats the mode ("calibrado (calibrado, ...)") adds nothing.
  const detailParts = markers.filter((marker) => marker !== modeLabel).join(" / ");
  const detail = [detailParts, routeScoreLabel === null ? null : `puntaje ${routeScoreLabel}`]
    .filter((value): value is string => Boolean(value))
    .join(", ");

  const name = modeLabel ?? "sin puntaje";
  return detail.length > 0 ? `${name} (${detail})` : name;
}

/**
 * A policy outcome ("routing_mode=premium_only;denied=…;outcome_evidence=…") as the operator reads
 * it: the routing mode and whether it denied. The rest is the gateway's bookkeeping, never shown.
 */
function policyOutcomeLabel(outcome: string | null) {
  const parts: string[] = [];
  for (const part of (outcome ?? "").split(";")) {
    if (part.startsWith("routing_mode=")) {
      parts.push(routingModeLabel(part.slice("routing_mode=".length)));
    } else if (part.startsWith("denied=")) {
      parts.push("denegado");
    }
  }
  return parts.length > 0 ? parts.join(", ") : "ninguna";
}

function renderChangedRequestSummary(change: PolicySimulationChangedRequest) {
  const routeChanged = change.baseline_route_target !== change.simulated_route_target;
  const tierChanged = change.baseline_tier !== change.simulated_tier;
  const statusChanged = change.baseline_terminal_status !== change.simulated_terminal_status;
  // Compared as read: two outcomes that differ only in bookkeeping are no change to show.
  const baselineOutcome = policyOutcomeLabel(change.baseline_policy_outcome);
  const simulatedOutcome = policyOutcomeLabel(change.simulated_policy_outcome);
  const outcomeChanged = baselineOutcome !== simulatedOutcome;
  const costChanged = change.baseline_estimated_cost !== change.simulated_estimated_cost;

  const highlights: string[] = [];
  if (routeChanged) {
    highlights.push(`ruta ${routeLabel(change.baseline_route_target)} → ${routeLabel(change.simulated_route_target)}`);
  }
  if (tierChanged) {
    highlights.push(`nivel ${change.baseline_tier ?? "—"} → ${change.simulated_tier ?? "—"}`);
  }
  if (statusChanged) {
    highlights.push(
      `estado ${statusLabel(change.baseline_terminal_status)} → ${statusLabel(change.simulated_terminal_status)}`,
    );
  }
  if (outcomeChanged) {
    highlights.push(`política ${baselineOutcome} → ${simulatedOutcome}`);
  }
  if (costChanged) {
    highlights.push(`costo ${formatUsd(change.baseline_estimated_cost, 4)} → ${formatUsd(change.simulated_estimated_cost, 4)}`);
  }

  return highlights.join(" · ");
}

function renderChangedRequestParity(change: PolicySimulationChangedRequest) {
  return `paridad de ruteo: ${formatRoutingState(
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

/**
 * Rows per tier, actual → draft. A row served from the cache or denied has no tier, so the last
 * row holds the rest and each column adds up to the evaluated rows.
 */
function tierCountItems(summary: PolicySimulationOutcomeCounts): ReadoutItem[] {
  const untiered = (counts: TierCounts) =>
    summary.evaluated_rows - TIERS.reduce((total, tier) => total + counts[tier], 0);

  return [
    ...TIERS.map((tier) => ({
      label: tier,
      value: `${summary.baseline_tier_counts[tier]} → ${summary.simulated_tier_counts[tier]}`,
    })),
    {
      label: "Caché o denegado",
      value: `${untiered(summary.baseline_tier_counts)} → ${untiered(summary.simulated_tier_counts)}`,
    },
  ];
}

function getDecisionSummary(simulationResult: PolicySimulationResponse) {
  const { summary, window, changed_requests: changedRequests } = simulationResult;
  const changedCount = changedRequests.length;

  if (window.returned_rows === 0 || summary.evaluated_rows === 0) {
    return {
      tone: "amber" as const,
      badge: "Sin ventana",
      title: "No hay tráfico reciente para comparar.",
      body: null,
    };
  }

  if (changedCount === 0) {
    return {
      tone: "emerald" as const,
      badge: "Sin cambios",
      title: "El borrador no cambia los pedidos de la muestra.",
      body: null,
    };
  }

  const consequenceParts: string[] = [];
  if (summary.changed_routes > 0) {
    consequenceParts.push(
      `${summary.changed_routes} ${summary.changed_routes === 1 ? "pedido rutearía" : "pedidos rutearían"} distinto`,
    );
  }
  if (summary.newly_denied > 0) {
    consequenceParts.push(
      `${summary.newly_denied} ${summary.newly_denied === 1 ? "pedido quedaría denegado" : "pedidos quedarían denegados"}`,
    );
  }
  if (summary.premium_cost_delta > 0) {
    consequenceParts.push(`el gasto premium subiría ${formatUsd(summary.premium_cost_delta, 4)}`);
  } else if (summary.premium_cost_delta < 0) {
    consequenceParts.push(`el gasto premium bajaría ${formatUsd(Math.abs(summary.premium_cost_delta), 4)}`);
  }

  const consequenceLabel =
    consequenceParts.length > 0
      ? consequenceParts.join("; ")
      : `${changedCount} ${changedCount === 1 ? "pedido cambiaría" : "pedidos cambiarían"}`;

  return {
    tone: summary.newly_denied > 0 ? ("rose" as const) : ("sky" as const),
    badge: summary.newly_denied > 0 ? "Revisar antes de guardar" : "Cambia resultados",
    title: `Este borrador cambiaría ${changedCount} ${changedCount === 1 ? "pedido" : "pedidos"} de la muestra.`,
    body: `${consequenceLabel.charAt(0).toUpperCase()}${consequenceLabel.slice(1)}.`,
  };
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
  const [fieldErrors, setFieldErrors] = useState<PolicyFormErrors>({});
  const [saveError, setSaveError] = useState<unknown>(null);
  // "Política guardada." stays until the next edit; the refetch after a save does not clear it.
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setFormState(toFormState(initialPolicy));
    setFieldErrors({});
    setSaveError(null);
  }, [initialPolicy]);

  const storedState = useMemo(() => toFormState(initialPolicy), [initialPolicy]);
  const dirty = policyFormChanged(formState, storedState);
  const runtimeEnforcedFields = useMemo(
    () => new Set(options.runtime_enforced_fields),
    [options.runtime_enforced_fields],
  );
  const softSignalFields = useMemo(() => new Set(options.soft_signal_fields), [options.soft_signal_fields]);
  const hiddenFields = useMemo(
    () =>
      new Set(
        (Object.keys(FIELD_GATES) as PolicyFormField[]).filter((field) => {
          const gate = FIELD_GATES[field];
          return !(gate.soft ? softSignalFields : runtimeEnforcedFields).has(gate.field);
        }),
      ),
    [runtimeEnforcedFields, softSignalFields],
  );
  const shown = (field: PolicyFormField) => !hiddenFields.has(field);
  const hardBudgetConfigured = formState.hardBudgetLimitUsd.trim().length > 0;
  const previewDecision = simulationResult ? getDecisionSummary(simulationResult) : null;
  const invalidFields = (Object.keys(FIELD_LABELS) as PolicyFormField[]).filter((field) => fieldErrors[field]);

  // The one check behind Guardar and Simular: the policy to send, or null with the errors shown.
  function validate(): TenantPolicy | null {
    setSaveError(null);
    const { errors, payload } = validatePolicyForm(formState, hiddenFields);
    setFieldErrors(errors);
    return payload === null ? null : toPolicy(payload);
  }

  // The form edits some fields; the rest (the capture flags, a field it does not show) stay as stored.
  function toPolicy(payload: Partial<TenantPolicyPayload>): TenantPolicy {
    const policy: TenantPolicy = { ...initialPolicy, ...payload };
    // A stored target finer than a hundredth shows rounded: it stays as stored unless the operator
    // changed the number.
    const targetUntouched =
      parsePolicyNumber(formState.routingQualityTarget) === parsePolicyNumber(storedState.routingQualityTarget);
    if (targetUntouched && initialPolicy.routing_quality_target !== undefined) {
      policy.routing_quality_target = initialPolicy.routing_quality_target;
    }
    return policy;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);

    const nextPolicy = validate();
    if (nextPolicy === null) {
      return;
    }

    try {
      await onSave(nextPolicy);
      setSaved(true);
    } catch (nextError) {
      setSaveError(nextError);
    }
  }

  async function handleSimulate() {
    const nextPolicy = validate();
    if (nextPolicy === null) {
      return;
    }

    await onSimulate(nextPolicy).catch(() => {
      // Surface the simulation mutation error via the dedicated preview panel state.
    });
  }

  function discardChanges() {
    setFormState(storedState);
    setFieldErrors({});
    setSaveError(null);
    setSaved(false);
  }

  // Any edit takes the confirmation away and the edited field's error with it.
  const set = <K extends keyof PolicyFormState>(key: K, value: PolicyFormState[K]) => {
    setFormState((current) => ({ ...current, [key]: value }));
    setSaved(false);
    setFieldErrors((current) => {
      if (current[key] === undefined) {
        return current;
      }
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  return (
    <form onSubmit={handleSubmit} aria-label={`Política de ${tenantName}`}>
      <div className="grid xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="flex min-w-0 flex-col gap-8 px-6 py-6">
          <FormSection title="Ruteo">
            {shown("routingQualityTarget") ? (
              <Field
                id="routing-quality-target"
                label={FIELD_LABELS.routingQualityTarget}
                error={fieldErrors.routingQualityTarget}
                hint={`${formatTarget(TARGET_MIN)} a ${formatTarget(TARGET_MAX)}: el router elige el punto más barato que lo cumple; ${formatTarget(TARGET_MAX)} manda todo a frontier.`}
              >
                {(control) => (
                  <input
                    {...control}
                    className="field-input max-w-40"
                    inputMode="decimal"
                    value={formState.routingQualityTarget}
                    onChange={(event) => set("routingQualityTarget", event.target.value)}
                  />
                )}
              </Field>
            ) : null}
            {shown("routingModeDefault") ? (
              <Field id="routing-mode-default" label={FIELD_LABELS.routingModeDefault}>
                {(control) => (
                  <select
                    {...control}
                    className="field-input max-w-60"
                    value={formState.routingModeDefault}
                    onChange={(event) => set("routingModeDefault", event.target.value as TenantPolicy["routing_mode_default"])}
                  >
                    {options.routing_modes.map((routingMode) => (
                      <option key={routingMode} value={routingMode}>
                        {routingModeLabel(routingMode)}
                      </option>
                    ))}
                  </select>
                )}
              </Field>
            ) : null}
            {shown("calibratedRoutingEnabled") ? (
              <Check
                label={FIELD_LABELS.calibratedRoutingEnabled}
                hint="Si se apaga, el tráfico automático va a local."
                checked={formState.calibratedRoutingEnabled}
                onChange={(checked) => set("calibratedRoutingEnabled", checked)}
              />
            ) : null}
            {shown("fallbackEnabled") ? (
              <Check
                label={FIELD_LABELS.fallbackEnabled}
                checked={formState.fallbackEnabled}
                onChange={(checked) => set("fallbackEnabled", checked)}
              />
            ) : null}
          </FormSection>

          <FormSection title="Límites">
            {shown("rateLimitRequestsPerMinute") ? (
              <Field
                id="rate-limit-rpm"
                label={FIELD_LABELS.rateLimitRequestsPerMinute}
                error={fieldErrors.rateLimitRequestsPerMinute}
                hint="Sobre el límite el gateway responde 429 con Retry-After."
              >
                {(control) => (
                  <input
                    {...control}
                    className="field-input max-w-40"
                    inputMode="numeric"
                    placeholder="Sin límite"
                    value={formState.rateLimitRequestsPerMinute}
                    onChange={(event) => set("rateLimitRequestsPerMinute", event.target.value)}
                  />
                )}
              </Field>
            ) : null}
            {shown("maxPremiumCostPerRequest") ? (
              <Field
                id="max-premium-cost"
                label={FIELD_LABELS.maxPremiumCostPerRequest}
                error={fieldErrors.maxPremiumCostPerRequest}
              >
                {(control) => (
                  <input
                    {...control}
                    className="field-input max-w-40"
                    inputMode="decimal"
                    placeholder="Sin límite"
                    value={formState.maxPremiumCostPerRequest}
                    onChange={(event) => set("maxPremiumCostPerRequest", event.target.value)}
                  />
                )}
              </Field>
            ) : null}
            <div className="grid gap-4 sm:grid-cols-2">
              {shown("hardBudgetLimitUsd") ? (
                <Field
                  id="hard-budget-limit-usd"
                  label={FIELD_LABELS.hardBudgetLimitUsd}
                  error={fieldErrors.hardBudgetLimitUsd}
                  hint="Vacío: sin límite."
                >
                  {(control) => (
                    <input
                      {...control}
                      className="field-input"
                      inputMode="decimal"
                      value={formState.hardBudgetLimitUsd}
                      onChange={(event) => set("hardBudgetLimitUsd", event.target.value)}
                    />
                  )}
                </Field>
              ) : null}
              {shown("hardBudgetEnforcement") ? (
                <Field
                  id="hard-budget-enforcement"
                  label={FIELD_LABELS.hardBudgetEnforcement}
                  hint={hardBudgetConfigured ? undefined : "Primero definir el presupuesto duro."}
                >
                  {(control) => (
                    <select
                      {...control}
                      className="field-input"
                      value={formState.hardBudgetEnforcement}
                      disabled={!hardBudgetConfigured}
                      onChange={(event) =>
                        set("hardBudgetEnforcement", event.target.value as NonNullable<TenantPolicy["hard_budget_enforcement"]>)
                      }
                    >
                      <option value="downgrade">Degradar a local el tráfico automático</option>
                      <option value="deny">Denegar el tráfico premium</option>
                    </select>
                  )}
                </Field>
              ) : null}
            </div>
            {shown("softBudgetUsd") ? (
              <Field
                id="soft-budget-usd"
                label={FIELD_LABELS.softBudgetUsd}
                error={fieldErrors.softBudgetUsd}
                hint="Solo aviso: no bloquea ni degrada."
              >
                {(control) => (
                  <input
                    {...control}
                    className="field-input max-w-40"
                    inputMode="decimal"
                    placeholder="Sin límite"
                    value={formState.softBudgetUsd}
                    onChange={(event) => set("softBudgetUsd", event.target.value)}
                  />
                )}
              </Field>
            ) : null}
          </FormSection>

          {shown("semanticCacheEnabled") ? (
            <FormSection title="Caché semántico">
              <Check
                label={FIELD_LABELS.semanticCacheEnabled}
                checked={formState.semanticCacheEnabled}
                onChange={(checked) => set("semanticCacheEnabled", checked)}
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <Field
                  id="semantic-cache-similarity-threshold"
                  label={FIELD_LABELS.semanticCacheSimilarityThreshold}
                  error={fieldErrors.semanticCacheSimilarityThreshold}
                  hint="0 a 1, por cada búsqueda."
                >
                  {(control) => (
                    <input
                      {...control}
                      className="field-input"
                      inputMode="decimal"
                      value={formState.semanticCacheSimilarityThreshold}
                      onChange={(event) => set("semanticCacheSimilarityThreshold", event.target.value)}
                    />
                  )}
                </Field>
                <Field
                  id="semantic-cache-max-entry-age-hours"
                  label={FIELD_LABELS.semanticCacheMaxEntryAgeHours}
                  error={fieldErrors.semanticCacheMaxEntryAgeHours}
                  hint="Entre 1 y 720."
                >
                  {(control) => (
                    <input
                      {...control}
                      className="field-input"
                      inputMode="numeric"
                      value={formState.semanticCacheMaxEntryAgeHours}
                      onChange={(event) => set("semanticCacheMaxEntryAgeHours", event.target.value)}
                    />
                  )}
                </Field>
              </div>
            </FormSection>
          ) : null}

          {shown("allowedPremiumModels") ? (
            <FormSection title={FIELD_LABELS.allowedPremiumModels}>
              <ModelAllowlistInput
                knownModels={options.known_premium_models}
                value={formState.allowedPremiumModels}
                onChange={(nextValue) => set("allowedPremiumModels", nextValue)}
                errorId={fieldErrors.allowedPremiumModels ? "allowed-premium-models-error" : undefined}
              />
              {fieldErrors.allowedPremiumModels ? (
                <p id="allowed-premium-models-error" className="m-0 text-[13px] font-medium text-danger">
                  {fieldErrors.allowedPremiumModels}
                </p>
              ) : null}
            </FormSection>
          ) : null}

          {shown("evidenceRetentionWindow") || shown("metadataMinimizationLevel") ? (
            <FormSection title="Evidencia">
              <div className="grid gap-4 sm:grid-cols-2">
                {shown("evidenceRetentionWindow") ? (
                  <Field id="evidence-retention-window" label={FIELD_LABELS.evidenceRetentionWindow}>
                    {(control) => (
                      <select
                        {...control}
                        className="field-input"
                        value={formState.evidenceRetentionWindow}
                        onChange={(event) =>
                          set("evidenceRetentionWindow", event.target.value as TenantPolicy["evidence_retention_window"])
                        }
                      >
                        <option value="24h">24 h</option>
                        <option value="7d">7 días</option>
                        <option value="30d">30 días</option>
                        <option value="90d">90 días</option>
                      </select>
                    )}
                  </Field>
                ) : null}
                {shown("metadataMinimizationLevel") ? (
                  <Field
                    id="metadata-minimization-level"
                    label={FIELD_LABELS.metadataMinimizationLevel}
                    hint="Estricta no guarda las señales de ruteo."
                  >
                    {(control) => (
                      <select
                        {...control}
                        className="field-input"
                        value={formState.metadataMinimizationLevel}
                        onChange={(event) =>
                          set("metadataMinimizationLevel", event.target.value as TenantPolicy["metadata_minimization_level"])
                        }
                      >
                        <option value="standard">Estándar</option>
                        <option value="strict">Estricta</option>
                      </select>
                    )}
                  </Field>
                ) : null}
              </div>
            </FormSection>
          ) : null}
        </div>

        <aside className="border-t border-line xl:border-t-0 xl:border-l" aria-labelledby="policy-preview-heading">
          <div className="flex flex-col gap-4 px-6 py-6 xl:sticky xl:top-0" aria-live="polite">
            <div className="flex items-baseline justify-between gap-3">
              <h2 id="policy-preview-heading" className="m-0 text-lg font-semibold text-ink">
                Vista previa
              </h2>
              {dirty ? (
                <span className="inline-flex items-center gap-1.5 font-label text-[13px] font-semibold text-warn">
                  <AlertCircle aria-hidden className="size-3.5" />
                  Cambios sin guardar
                </span>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" disabled={isSaving || isSimulating} onClick={() => void handleSimulate()}>
                {isSimulating ? <LoaderCircle aria-hidden className="size-4 animate-spin" /> : <Telescope aria-hidden className="size-4" />}
                Simular
              </Button>
              <Button type="submit" disabled={!dirty || isSaving || isSimulating}>
                {isSaving ? <LoaderCircle aria-hidden className="size-4 animate-spin" /> : <Save aria-hidden className="size-4" />}
                Guardar política
              </Button>
              <Button
                type="button"
                variant="ghost"
                disabled={!dirty || isSaving || isSimulating}
                onClick={discardChanges}
              >
                <RotateCcw aria-hidden className="size-4" />
                Descartar cambios
              </Button>
            </div>

            {saved ? (
              <Alert variant="success" role="status">
                <AlertDescription>Política guardada.</AlertDescription>
              </Alert>
            ) : null}
            {invalidFields.length > 0 ? (
              <ErrorAlert
                error={`Revisar los campos: ${invalidFields.map((field) => FIELD_LABELS[field]).join(", ")}.`}
                fallback="Revisar los campos."
              />
            ) : null}
            {saveError ? <ErrorAlert error={saveError} fallback="No se pudo guardar la política." /> : null}

            {isSimulating ? <LoadingRows rows={3} label="Simulando el borrador" /> : null}
            {simulationError ? (
              <ErrorAlert error={`La simulación falló: ${simulationError}`} fallback="La simulación falló." />
            ) : null}
            {!isSimulating && !simulationError && !simulationResult ? (
              <p className="m-0 border border-dashed border-line px-4 py-4 text-sm text-ink-3">
                Simular para comparar el borrador con el tráfico reciente antes de guardar.
              </p>
            ) : null}

            {simulationResult && previewDecision ? (
              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-1 border-y border-line-strong py-3">
                  <span className="font-label text-[13px] font-semibold text-ink-3">{previewDecision.badge}</span>
                  <h3 className="m-0 text-base font-semibold text-ink">{previewDecision.title}</h3>
                  {previewDecision.body ? <p className="m-0 text-sm text-ink-2">{previewDecision.body}</p> : null}
                </div>
                <Readout
                  items={[
                    { label: "Pedidos evaluados", value: String(simulationResult.summary.evaluated_rows) },
                    { label: "Rutas que cambian", value: String(simulationResult.summary.changed_routes) },
                    { label: "Nuevas denegaciones", value: String(simulationResult.summary.newly_denied) },
                    { label: "Δ costo premium", value: formatUsd(simulationResult.summary.premium_cost_delta, 4) },
                  ]}
                />
                {simulationResult.summary.evaluated_rows > 0 ? (
                  <section aria-labelledby="tier-counts-heading" className="flex flex-col gap-2">
                    <h3 id="tier-counts-heading" className="m-0 font-label text-[13px] font-semibold text-ink-2">
                      Pedidos por nivel: actual → borrador
                    </h3>
                    <Readout items={tierCountItems(simulationResult.summary)} />
                    <p className="m-0 text-[13px] text-ink-3">
                      {`${simulationResult.summary.learned_router_rows} con el router aprendido · ${simulationResult.summary.heuristic_rows} con la heurística`}
                    </p>
                  </section>
                ) : null}
                <p className="m-0 text-[13px] text-ink-3">
                  {`Comparado contra ${simulationResult.window.returned_rows} pedidos recientes. No se guardó nada.`}
                </p>
                {simulationResult.window.returned_rows === 0 ? (
                  <Alert variant="warning">
                    <AlertDescription>No hubo tráfico reciente en la ventana de la simulación.</AlertDescription>
                  </Alert>
                ) : simulationResult.changed_requests.length === 0 ? (
                  <Alert variant="success" role="status">
                    <AlertDescription>Ningún pedido cambia de resultado en esta ventana.</AlertDescription>
                  </Alert>
                ) : (
                  <section aria-labelledby="changed-sample-heading" className="flex flex-col gap-2">
                    <h3 id="changed-sample-heading" className="m-0 font-label text-[13px] font-semibold text-ink-2">
                      Pedidos que cambian
                    </h3>
                    <ul className="m-0 flex list-none flex-col divide-y divide-line border-y border-line p-0">
                      {simulationResult.changed_requests.map((change) => (
                        <li key={change.request_id} className="flex flex-col gap-1 py-2.5">
                          <div className="flex flex-wrap items-center gap-2 text-sm">
                            <span className="font-mono text-[12px] text-ink-2">{change.request_id}</span>
                            <span className="font-mono text-[12px] text-ink-3">{change.requested_model}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm font-medium text-ink">
                            <span>{routeLabel(change.baseline_route_target)}</span>
                            <ArrowRight aria-hidden className="size-3.5 text-ink-3" />
                            <span>{routeLabel(change.simulated_route_target)}</span>
                          </div>
                          <p className="m-0 text-[13px] text-ink-2">{renderChangedRequestSummary(change)}</p>
                          <p className="m-0 text-[12px] text-ink-3">{renderChangedRequestParity(change)}</p>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
                {simulationResult.approximation_notes.length > 0 ? (
                  <div className="text-[13px] text-ink-3">
                    <div className="font-semibold text-ink-2">Notas de la simulación</div>
                    <ul className="mt-1 list-disc pl-5">
                      {simulationResult.approximation_notes.map((note, index) => (
                        <li key={simulationResult.approximation_note_codes[index] ?? note}>
                          {approximationNoteLabel(simulationResult.approximation_note_codes[index], note)}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </aside>
      </div>
    </form>
  );
}

function FormSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <h2 className="m-0 border-b border-line pb-2 text-lg font-semibold text-ink">{title}</h2>
      {children}
    </section>
  );
}

type FieldControlProps = {
  id: string;
  "aria-describedby"?: string;
  "aria-invalid"?: true;
};

/**
 * A labelled control with its hint and its error linked to it (`aria-describedby`), so a screen
 * reader says them with the field. The control comes from the render function with those props.
 */
function Field({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: (control: FieldControlProps) => ReactNode;
}) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(" ");

  return (
    <div>
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      {children({
        id,
        "aria-describedby": describedBy || undefined,
        "aria-invalid": error ? true : undefined,
      })}
      {error ? (
        <p id={errorId} className="mt-1.5 text-[13px] font-medium text-danger">
          {error}
        </p>
      ) : null}
      {hint ? (
        <p id={hintId} className="mt-1.5 text-[13px] text-ink-3">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

function Check({
  label,
  hint,
  checked,
  onChange,
}: {
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  const hintId = useId();

  return (
    <div>
      <label className="flex items-center gap-2.5 text-[15px] font-medium text-ink">
        <input
          type="checkbox"
          className="size-4 accent-ink"
          checked={checked}
          aria-describedby={hint ? hintId : undefined}
          onChange={(event) => onChange(event.target.checked)}
        />
        {label}
      </label>
      {hint ? (
        <p id={hintId} className="mt-1 ml-[26px] text-[13px] text-ink-3">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
