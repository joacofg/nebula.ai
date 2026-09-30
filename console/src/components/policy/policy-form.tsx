"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { AlertCircle, ArrowRight, LoaderCircle, RotateCcw, Save, Telescope } from "lucide-react";

import type {
  PolicyOptionsResponse,
  PolicySimulationChangedRequest,
  PolicySimulationResponse,
  TenantPolicy,
} from "@/lib/admin-api";
import { ModelAllowlistInput } from "@/components/policy/model-allowlist-input";
import { Readout } from "@/components/system/readout";
import { LoadingRows } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

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
  evidenceRetentionWindow: TenantPolicy["evidence_retention_window"];
  metadataMinimizationLevel: TenantPolicy["metadata_minimization_level"];
  routingQualityTarget: string;
  rateLimitRequestsPerMinute: string;
};

// Gateway default (TenantPolicy.routing_quality_target) for policies saved before the field existed.
const DEFAULT_ROUTING_QUALITY_TARGET = 0.95;

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
    evidenceRetentionWindow: policy.evidence_retention_window,
    metadataMinimizationLevel: policy.metadata_minimization_level,
    routingQualityTarget: (policy.routing_quality_target ?? DEFAULT_ROUTING_QUALITY_TARGET).toString(),
    rateLimitRequestsPerMinute: policy.rate_limit_requests_per_minute?.toString() ?? "",
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
    evidence_retention_window: state.evidenceRetentionWindow,
    metadata_minimization_level: state.metadataMinimizationLevel,
    routing_quality_target: Number(state.routingQualityTarget),
    rate_limit_requests_per_minute:
      state.rateLimitRequestsPerMinute.trim() === "" ? null : Number(state.rateLimitRequestsPerMinute),
  };
}

function formatUsd(value: number) {
  return `${value < 0 ? "−" : ""}USD ${Math.abs(value).toFixed(4)}`;
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
    highlights.push(`ruta ${change.baseline_route_target} → ${change.simulated_route_target}`);
  }
  if (statusChanged) {
    highlights.push(`estado ${change.baseline_terminal_status} → ${change.simulated_terminal_status}`);
  }
  if (outcomeChanged) {
    highlights.push(
      `política ${(change.baseline_policy_outcome ?? "ninguna")} → ${(change.simulated_policy_outcome ?? "ninguna")}`,
    );
  }
  if (costChanged) {
    highlights.push(`costo ${formatUsd(change.baseline_estimated_cost)} → ${formatUsd(change.simulated_estimated_cost)}`);
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
    consequenceParts.push(`el gasto premium subiría ${formatUsd(summary.premium_cost_delta)}`);
  } else if (summary.premium_cost_delta < 0) {
    consequenceParts.push(`el gasto premium bajaría ${formatUsd(Math.abs(summary.premium_cost_delta))}`);
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
  const rateLimitText = formState.rateLimitRequestsPerMinute.trim();
  const rateLimitValid =
    rateLimitText === "" ||
    (/^\d+$/.test(rateLimitText) && Number(rateLimitText) >= 1 && Number(rateLimitText) <= 100000);
  const qualityTargetText = formState.routingQualityTarget.trim();
  const qualityTargetValue = qualityTargetText === "" ? Number.NaN : Number(qualityTargetText);
  const previewDecision = simulationResult ? getDecisionSummary(simulationResult) : null;
  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const nextPolicy = toPolicyPayload(formState, initialPolicy);
    if (nextPolicy.allowed_premium_models.length === 0) {
      setError("Elegir al menos un modelo premium.");
      return;
    }
    if (!Number.isFinite(cacheThresholdValue) || cacheThresholdValue < 0 || cacheThresholdValue > 1) {
      setError("El umbral de similitud tiene que estar entre 0 y 1.");
      return;
    }
    if (!rateLimitValid) {
      setError("El límite tiene que ser un entero entre 1 y 100000 pedidos por minuto.");
      return;
    }
    if (!Number.isInteger(cacheMaxAgeValue) || cacheMaxAgeValue < 1 || cacheMaxAgeValue > 720) {
      setError("La antigüedad máxima tiene que ser un entero entre 1 y 720 horas.");
      return;
    }
    if (!Number.isFinite(qualityTargetValue) || qualityTargetValue < 0.5 || qualityTargetValue > 1) {
      setError("El objetivo de calidad tiene que estar entre 0.5 y 1.");
      return;
    }

    await onSave(nextPolicy).catch((nextError) => {
      setError(nextError instanceof Error ? nextError.message : "No se pudo guardar la política.");
    });
  }

  async function handleSimulate() {
    setError(null);

    const nextPolicy = toPolicyPayload(formState, initialPolicy);
    if (nextPolicy.allowed_premium_models.length === 0) {
      setError("Elegir al menos un modelo premium.");
      return;
    }
    if (!Number.isFinite(cacheThresholdValue) || cacheThresholdValue < 0 || cacheThresholdValue > 1) {
      setError("El umbral de similitud tiene que estar entre 0 y 1.");
      return;
    }
    if (!Number.isInteger(cacheMaxAgeValue) || cacheMaxAgeValue < 1 || cacheMaxAgeValue > 720) {
      setError("La antigüedad máxima tiene que ser un entero entre 1 y 720 horas.");
      return;
    }
    if (!Number.isFinite(qualityTargetValue) || qualityTargetValue < 0.5 || qualityTargetValue > 1) {
      setError("El objetivo de calidad tiene que estar entre 0.5 y 1.");
      return;
    }

    await onSimulate(nextPolicy).catch(() => {
      // Surface the simulation mutation error via the dedicated preview panel state.
    });
  }


  const set = <K extends keyof PolicyFormState>(key: K, value: PolicyFormState[K]) =>
    setFormState((current) => ({ ...current, [key]: value }));
  const has = (field: string) => runtimeEnforcedFields.has(field);

  return (
    <form onSubmit={handleSubmit} aria-label={`Política de ${tenantName}`}>
      <div className="grid xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="flex min-w-0 flex-col gap-8 px-6 py-6">
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <FormSection title="Ruteo">
            {has("routing_quality_target") ? (
              <Field id="routing-quality-target" label="Objetivo de calidad" hint="0.5 a 1.0: el router elige el punto más barato que lo cumple; 1.0 manda todo a frontier.">
                <input
                  id="routing-quality-target"
                  className="field-input max-w-40"
                  inputMode="decimal"
                  value={formState.routingQualityTarget}
                  onChange={(event) => set("routingQualityTarget", event.target.value)}
                />
              </Field>
            ) : null}
            {has("routing_mode_default") ? (
              <Field id="routing-mode-default" label="Modo de ruteo">
                <select
                  id="routing-mode-default"
                  className="field-input max-w-60"
                  value={formState.routingModeDefault}
                  onChange={(event) => set("routingModeDefault", event.target.value as TenantPolicy["routing_mode_default"])}
                >
                  {options.routing_modes.map((routingMode) => (
                    <option key={routingMode} value={routingMode}>
                      {routingMode}
                    </option>
                  ))}
                </select>
              </Field>
            ) : null}
            {has("calibrated_routing_enabled") ? (
              <Check
                label="Ruteo calibrado (heurística v0)"
                hint="Apagado, el tráfico automático va a local."
                checked={formState.calibratedRoutingEnabled}
                onChange={(checked) => set("calibratedRoutingEnabled", checked)}
              />
            ) : null}
            {has("fallback_enabled") ? (
              <Check
                label="Fallback a premium si falla el local"
                checked={formState.fallbackEnabled}
                onChange={(checked) => set("fallbackEnabled", checked)}
              />
            ) : null}
          </FormSection>

          <FormSection title="Límites">
            {has("rate_limit_requests_per_minute") ? (
              <Field id="rate-limit-rpm" label="Límite de pedidos por minuto" hint="Sobre el límite el gateway responde 429 con Retry-After.">
                <input
                  id="rate-limit-rpm"
                  className="field-input max-w-40"
                  inputMode="numeric"
                  placeholder="Sin límite"
                  value={formState.rateLimitRequestsPerMinute}
                  onChange={(event) => set("rateLimitRequestsPerMinute", event.target.value)}
                />
              </Field>
            ) : null}
            {has("max_premium_cost_per_request") ? (
              <Field id="max-premium-cost" label="Costo premium máximo por pedido (USD)">
                <input
                  id="max-premium-cost"
                  className="field-input max-w-40"
                  inputMode="decimal"
                  value={formState.maxPremiumCostPerRequest}
                  onChange={(event) => set("maxPremiumCostPerRequest", event.target.value)}
                />
              </Field>
            ) : null}
            <div className="grid gap-4 sm:grid-cols-2">
              {has("hard_budget_limit_usd") ? (
                <Field id="hard-budget-limit-usd" label="Presupuesto duro acumulado (USD)" hint="Vacío: sin límite.">
                  <input
                    id="hard-budget-limit-usd"
                    className="field-input"
                    inputMode="decimal"
                    value={formState.hardBudgetLimitUsd}
                    onChange={(event) => set("hardBudgetLimitUsd", event.target.value)}
                  />
                </Field>
              ) : null}
              {has("hard_budget_enforcement") ? (
                <Field
                  id="hard-budget-enforcement"
                  label="Al agotarse el presupuesto"
                  hint={hardBudgetConfigured ? undefined : "Primero definir el presupuesto duro."}
                >
                  <select
                    id="hard-budget-enforcement"
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
                </Field>
              ) : null}
            </div>
            {softSignalFields.has("soft_budget_usd") ? (
              <Field id="soft-budget-usd" label="Presupuesto blando (USD)" hint="Solo aviso: no bloquea ni degrada.">
                <input
                  id="soft-budget-usd"
                  className="field-input max-w-40"
                  inputMode="decimal"
                  value={formState.softBudgetUsd}
                  onChange={(event) => set("softBudgetUsd", event.target.value)}
                />
              </Field>
            ) : null}
          </FormSection>

          {has("semantic_cache_enabled") ? (
            <FormSection title="Caché semántico">
              <Check
                label="Caché semántico activado"
                checked={formState.semanticCacheEnabled}
                onChange={(checked) => set("semanticCacheEnabled", checked)}
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <Field id="semantic-cache-similarity-threshold" label="Umbral de similitud" hint="0 a 1, por cada búsqueda.">
                  <input
                    id="semantic-cache-similarity-threshold"
                    className="field-input"
                    inputMode="decimal"
                    value={formState.semanticCacheSimilarityThreshold}
                    onChange={(event) => set("semanticCacheSimilarityThreshold", event.target.value)}
                  />
                </Field>
                <Field id="semantic-cache-max-entry-age-hours" label="Antigüedad máxima (h)" hint="Entre 1 y 720.">
                  <input
                    id="semantic-cache-max-entry-age-hours"
                    className="field-input"
                    inputMode="numeric"
                    value={formState.semanticCacheMaxEntryAgeHours}
                    onChange={(event) => set("semanticCacheMaxEntryAgeHours", event.target.value)}
                  />
                </Field>
              </div>
            </FormSection>
          ) : null}

          {has("allowed_premium_models") ? (
            <FormSection title="Modelos premium permitidos">
              <ModelAllowlistInput
                knownModels={options.known_premium_models}
                value={formState.allowedPremiumModels}
                onChange={(nextValue) => set("allowedPremiumModels", nextValue)}
              />
            </FormSection>
          ) : null}

          {has("evidence_retention_window") || has("metadata_minimization_level") ? (
            <FormSection title="Evidencia">
              <div className="grid gap-4 sm:grid-cols-2">
                {has("evidence_retention_window") ? (
                  <Field id="evidence-retention-window" label="Retención de evidencia">
                    <select
                      id="evidence-retention-window"
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
                  </Field>
                ) : null}
                {has("metadata_minimization_level") ? (
                  <Field id="metadata-minimization-level" label="Minimización de metadatos" hint="Estricta no guarda las señales de ruteo.">
                    <select
                      id="metadata-minimization-level"
                      className="field-input"
                      value={formState.metadataMinimizationLevel}
                      onChange={(event) =>
                        set("metadataMinimizationLevel", event.target.value as TenantPolicy["metadata_minimization_level"])
                      }
                    >
                      <option value="standard">Estándar</option>
                      <option value="strict">Estricta</option>
                    </select>
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
                onClick={() => setFormState(toFormState(initialPolicy))}
              >
                <RotateCcw aria-hidden className="size-4" />
                Descartar cambios
              </Button>
            </div>

            {isSimulating ? <LoadingRows rows={3} label="Simulando el borrador" /> : null}
            {simulationError ? (
              <Alert variant="destructive">
                <AlertDescription>La simulación falló: {simulationError}</AlertDescription>
              </Alert>
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
                    { label: "Δ costo premium", value: formatUsd(simulationResult.summary.premium_cost_delta) },
                  ]}
                />
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
                            <span>{change.baseline_route_target}</span>
                            <ArrowRight aria-hidden className="size-3.5 text-ink-3" />
                            <span>{change.simulated_route_target}</span>
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
                      {simulationResult.approximation_notes.map((note) => (
                        <li key={note}>{note}</li>
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

function Field({ id, label, hint, children }: { id: string; label: string; hint?: string; children: ReactNode }) {
  return (
    <div>
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      {children}
      {hint ? <p className="mt-1.5 text-[13px] text-ink-3">{hint}</p> : null}
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
  return (
    <div>
      <label className="flex items-center gap-2.5 text-[15px] font-medium text-ink">
        <input type="checkbox" className="size-4 accent-ink" checked={checked} onChange={(event) => onChange(event.target.checked)} />
        {label}
      </label>
      {hint ? <p className="mt-1 ml-[26px] text-[13px] text-ink-3">{hint}</p> : null}
    </div>
  );
}
