import { within } from "@testing-library/react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PolicyForm } from "@/components/policy/policy-form";
import type { PolicySimulationResponse, TenantPolicy } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const baseSimulationResult: PolicySimulationResponse = {
  tenant_id: "default",
  candidate_policy: {
    routing_mode_default: "premium_only",
    calibrated_routing_enabled: true,
    fallback_enabled: false,
    semantic_cache_enabled: true,
    semantic_cache_similarity_threshold: 0.9,
    semantic_cache_max_entry_age_hours: 168,
    allowed_premium_models: ["openai/gpt-4o-mini"],
    max_premium_cost_per_request: 0.5,
    hard_budget_limit_usd: 10,
    hard_budget_enforcement: "deny",
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
    evidence_retention_window: "30d",
    metadata_minimization_level: "standard",
    routing_quality_target: 0.95,
  },
  approximation_notes: ["Replay uses stored route signals rather than raw prompt text."],
  window: {
    requested_from: null,
    requested_to: null,
    evaluated_from: "2026-03-27T00:00:00Z",
    evaluated_to: "2026-03-28T00:00:00Z",
    requested_limit: 50,
    changed_sample_limit: 5,
    returned_rows: 2,
  },
  summary: {
    evaluated_rows: 2,
    changed_routes: 1,
    newly_denied: 1,
    baseline_premium_cost: 0.2,
    simulated_premium_cost: 0.3,
    premium_cost_delta: 0.1,
  },
  calibration_summary: {
    tenant_id: "default",
    scope: "tenant_window",
    state: "thin",
    state_reason: "Eligible calibrated routing evidence is still below the tenant sufficiency threshold.",
    generated_at: "2026-03-28T00:00:00Z",
    latest_eligible_request_at: "2026-03-28T00:00:00Z",
    latest_any_request_at: "2026-03-28T00:00:00Z",
    eligible_request_count: 2,
    sufficient_request_count: 2,
    thin_request_threshold: 5,
    staleness_threshold_hours: 24,
    excluded_request_count: 0,
    gated_request_count: 0,
    degraded_request_count: 0,
    excluded_reasons: [],
    gated_reasons: [],
    degraded_reasons: [],
  },
  changed_requests: [
    {
      request_id: "req-1",
      timestamp: "2026-03-27T12:00:00Z",
      requested_model: "openai/gpt-4o-mini",
      baseline_route_target: "local",
      simulated_route_target: "premium",
      baseline_terminal_status: "completed",
      simulated_terminal_status: "policy_denied",
      baseline_policy_outcome: "default",
      simulated_policy_outcome: "routing_mode=premium_only;denied=Request exceeds the tenant premium spend guardrail.",
      baseline_route_reason: "auto_local",
      simulated_route_reason: "explicit_premium_model",
      baseline_route_mode: "auto",
      simulated_route_mode: "premium_only",
      baseline_calibrated_routing: true,
      simulated_calibrated_routing: null,
      baseline_degraded_routing: false,
      simulated_degraded_routing: false,
      baseline_route_score: 0.61,
      simulated_route_score: null,
      baseline_estimated_cost: 0,
      simulated_estimated_cost: 0.1,
    },
  ],
};

function renderPolicyForm({
  onSave = vi.fn().mockResolvedValue(undefined),
  onSimulate = vi.fn().mockResolvedValue(undefined),
  simulationResult = null as PolicySimulationResponse | null,
  simulationError = null as string | null,
  isSimulating = false,
  runtimeEnforcedFields = null as string[] | null,
  policyOverrides = {} as Partial<TenantPolicy>,
} = {}) {
  return renderWithProviders(
    <PolicyForm
      tenantName="Default Workspace"
      initialPolicy={{
        routing_mode_default: "auto",
        calibrated_routing_enabled: true,
        fallback_enabled: true,
        semantic_cache_enabled: true,
        semantic_cache_similarity_threshold: 0.9,
        semantic_cache_max_entry_age_hours: 168,
        allowed_premium_models: ["openai/gpt-4o-mini"],
        max_premium_cost_per_request: null,
        hard_budget_limit_usd: null,
        hard_budget_enforcement: null,
        soft_budget_usd: null,
        prompt_capture_enabled: false,
        response_capture_enabled: false,
        evidence_retention_window: "30d",
        metadata_minimization_level: "standard",
        routing_quality_target: 0.95,
        ...policyOverrides,
      }}
      options={{
        routing_modes: ["auto", "local_only", "premium_only"],
        known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
        default_premium_model: "openai/gpt-4o-mini",
        runtime_enforced_fields: runtimeEnforcedFields ?? [
          "routing_quality_target",
          "rate_limit_requests_per_minute",
          "routing_mode_default",
          "calibrated_routing_enabled",
          "allowed_premium_models",
          "semantic_cache_enabled",
          "semantic_cache_similarity_threshold",
          "semantic_cache_max_entry_age_hours",
          "fallback_enabled",
          "max_premium_cost_per_request",
          "hard_budget_limit_usd",
          "hard_budget_enforcement",
          "evidence_retention_window",
          "metadata_minimization_level",
        ],
        soft_signal_fields: ["soft_budget_usd"],
        advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
      }}
      isSaving={false}
      isSimulating={isSimulating}
      simulationResult={simulationResult}
      simulationError={simulationError}
      onSimulate={onSimulate}
      onSave={onSave}
    />,
  );
}

describe("policy-form", () => {
  it("shows and clears dirty state with Reset changes", async () => {
    renderPolicyForm();

    await userEvent.selectOptions(screen.getByLabelText("Modo de ruteo"), "premium_only");
    expect(screen.getByText("Cambios sin guardar")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Descartar cambios" }));

    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
  });

  it("submits the updated policy payload", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    await userEvent.selectOptions(screen.getByLabelText("Modo de ruteo"), "premium_only");
    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
    await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
    await userEvent.type(screen.getByLabelText("Umbral de similitud"), "0.82");
    await userEvent.clear(screen.getByLabelText("Antigüedad máxima (h)"));
    await userEvent.type(screen.getByLabelText("Antigüedad máxima (h)"), "48");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          routing_mode_default: "premium_only",
          calibrated_routing_enabled: true,
          fallback_enabled: false,
          semantic_cache_similarity_threshold: 0.82,
          semantic_cache_max_entry_age_hours: 48,
        }),
      );
    });
  });

  it("sends the current draft to simulation without saving", async () => {
    const onSimulate = vi.fn().mockResolvedValue(undefined);
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSimulate, onSave });

    await userEvent.selectOptions(screen.getByLabelText("Modo de ruteo"), "premium_only");
    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
    await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
    await userEvent.type(screen.getByLabelText("Umbral de similitud"), "0.88");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    await waitFor(() => {
      expect(onSimulate).toHaveBeenCalledWith(
        expect.objectContaining({
          routing_mode_default: "premium_only",
          fallback_enabled: false,
          semantic_cache_similarity_threshold: 0.88,
        }),
      );
    });
    expect(onSave).not.toHaveBeenCalled();
  });

  it("renders a decision-first preview with the sample and an explicit save", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByText("Revisar antes de guardar")).toBeInTheDocument();
    expect(preview.getByText("Este borrador cambiaría 1 pedido de la muestra.")).toBeInTheDocument();
    expect(
      preview.getByText("1 pedido rutearía distinto; 1 pedido quedaría denegado; el gasto premium subiría USD 0.1000."),
    ).toBeInTheDocument();
    for (const name of ["Pedidos evaluados", "Rutas que cambian", "Nuevas denegaciones", "Δ costo premium"]) {
      expect(preview.getByRole("group", { name })).toBeInTheDocument();
    }
    expect(preview.getByText("Pedidos que cambian")).toBeInTheDocument();
    expect(preview.getByText("req-1")).toBeInTheDocument();
    expect(preview.getByText(/ruta local → premium/i)).toBeInTheDocument();
    expect(preview.getByText(/estado completed → policy_denied/i)).toBeInTheDocument();
    expect(preview.getByText(/paridad de ruteo: auto \(calibrated, score 0\.61\) → premium_only/i)).toBeInTheDocument();
    expect(preview.getByText(/Replay uses stored route signals rather than raw prompt text\./i)).toBeInTheDocument();
    expect(preview.getByText("Comparado contra 2 pedidos recientes. No se guardó nada.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar política" })).toBeInTheDocument();
  });

  it("keeps unchanged, empty, loading, and failed preview states explicit and non-saving", () => {
    const unchangedResult: PolicySimulationResponse = {
      ...baseSimulationResult,
      summary: {
        ...baseSimulationResult.summary,
        changed_routes: 0,
        newly_denied: 0,
        premium_cost_delta: 0,
      },
      changed_requests: [],
    };

    const { rerender } = renderPolicyForm({ simulationResult: unchangedResult });

    let previewSection = screen.getByRole("heading", { name: "Vista previa" }).closest("aside");
    expect(previewSection).not.toBeNull();
    let preview = within(previewSection as HTMLElement);

    expect(preview.getByText("Sin cambios")).toBeInTheDocument();
    expect(preview.getByText("El borrador no cambia los pedidos de la muestra.")).toBeInTheDocument();
    expect(preview.getByText("Ningún pedido cambia de resultado en esta ventana.")).toBeInTheDocument();
    expect(preview.getByText(/No se guardó nada\./i)).toBeInTheDocument();

    rerender(
      <PolicyForm
        tenantName="Default Workspace"
        initialPolicy={{
          routing_mode_default: "auto",
          calibrated_routing_enabled: true,
          fallback_enabled: true,
          semantic_cache_enabled: true,
          semantic_cache_similarity_threshold: 0.9,
          semantic_cache_max_entry_age_hours: 168,
          allowed_premium_models: ["openai/gpt-4o-mini"],
          max_premium_cost_per_request: null,
          hard_budget_limit_usd: null,
          hard_budget_enforcement: null,
          soft_budget_usd: null,
          prompt_capture_enabled: false,
          response_capture_enabled: false,
      evidence_retention_window: "30d",
      metadata_minimization_level: "standard",
      routing_quality_target: 0.95,
        }}
        options={{
          routing_modes: ["auto", "local_only", "premium_only"],
          known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
          default_premium_model: "openai/gpt-4o-mini",
          runtime_enforced_fields: [
            "routing_quality_target",
            "routing_mode_default",
            "calibrated_routing_enabled",
            "allowed_premium_models",
            "semantic_cache_enabled",
            "semantic_cache_similarity_threshold",
            "semantic_cache_max_entry_age_hours",
            "fallback_enabled",
            "max_premium_cost_per_request",
            "hard_budget_limit_usd",
            "hard_budget_enforcement",
          ],
          soft_signal_fields: ["soft_budget_usd"],
          advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
        }}
        isSaving={false}
        isSimulating={false}
        simulationResult={{
          ...baseSimulationResult,
          window: {
            ...baseSimulationResult.window,
            returned_rows: 0,
          },
          summary: {
            ...baseSimulationResult.summary,
            evaluated_rows: 0,
            changed_routes: 0,
            newly_denied: 0,
            premium_cost_delta: 0,
          },
          changed_requests: [],
        }}
        simulationError={null}
        onSimulate={vi.fn().mockResolvedValue(undefined)}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    previewSection = screen.getByRole("heading", { name: "Vista previa" }).closest("aside");
    expect(previewSection).not.toBeNull();
    preview = within(previewSection as HTMLElement);

    expect(preview.getByText("Sin ventana")).toBeInTheDocument();
    expect(preview.getByText("No hay tráfico reciente para comparar.")).toBeInTheDocument();
    expect(
      preview.getByText("No hubo tráfico reciente en la ventana de la simulación."),
    ).toBeInTheDocument();
    expect(preview.getByText(/No se guardó nada\./i)).toBeInTheDocument();

    rerender(
      <PolicyForm
        tenantName="Default Workspace"
        initialPolicy={{
          routing_mode_default: "auto",
          calibrated_routing_enabled: true,
          fallback_enabled: true,
          semantic_cache_enabled: true,
          semantic_cache_similarity_threshold: 0.9,
          semantic_cache_max_entry_age_hours: 168,
          allowed_premium_models: ["openai/gpt-4o-mini"],
          max_premium_cost_per_request: null,
          hard_budget_limit_usd: null,
          hard_budget_enforcement: null,
          soft_budget_usd: null,
          prompt_capture_enabled: false,
          response_capture_enabled: false,
      evidence_retention_window: "30d",
      metadata_minimization_level: "standard",
      routing_quality_target: 0.95,
        }}
        options={{
          routing_modes: ["auto", "local_only", "premium_only"],
          known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
          default_premium_model: "openai/gpt-4o-mini",
          runtime_enforced_fields: [
            "routing_quality_target",
            "routing_mode_default",
            "calibrated_routing_enabled",
            "allowed_premium_models",
            "semantic_cache_enabled",
            "semantic_cache_similarity_threshold",
            "semantic_cache_max_entry_age_hours",
            "fallback_enabled",
            "max_premium_cost_per_request",
            "hard_budget_limit_usd",
            "hard_budget_enforcement",
          ],
          soft_signal_fields: ["soft_budget_usd"],
          advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
        }}
        isSaving={false}
        isSimulating={true}
        simulationResult={null}
        simulationError={null}
        onSimulate={vi.fn().mockResolvedValue(undefined)}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByRole("status", { name: "Simulando el borrador" })).toBeInTheDocument();
    expect(screen.queryByText(/guardar política/i)).toBeInTheDocument();

    rerender(
      <PolicyForm
        tenantName="Default Workspace"
        initialPolicy={{
          routing_mode_default: "auto",
          calibrated_routing_enabled: true,
          fallback_enabled: true,
          semantic_cache_enabled: true,
          semantic_cache_similarity_threshold: 0.9,
          semantic_cache_max_entry_age_hours: 168,
          allowed_premium_models: ["openai/gpt-4o-mini"],
          max_premium_cost_per_request: null,
          hard_budget_limit_usd: null,
          hard_budget_enforcement: null,
          soft_budget_usd: null,
          prompt_capture_enabled: false,
          response_capture_enabled: false,
      evidence_retention_window: "30d",
      metadata_minimization_level: "standard",
      routing_quality_target: 0.95,
        }}
        options={{
          routing_modes: ["auto", "local_only", "premium_only"],
          known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
          default_premium_model: "openai/gpt-4o-mini",
          runtime_enforced_fields: [
            "routing_quality_target",
            "routing_mode_default",
            "allowed_premium_models",
            "semantic_cache_enabled",
            "semantic_cache_similarity_threshold",
            "semantic_cache_max_entry_age_hours",
            "fallback_enabled",
            "max_premium_cost_per_request",
          ],
          soft_signal_fields: ["soft_budget_usd"],
          advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
        }}
        isSaving={false}
        isSimulating={false}
        simulationResult={null}
        simulationError="Nebula admin request failed."
        onSimulate={vi.fn().mockResolvedValue(undefined)}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByText("La simulación falló: Nebula admin request failed.")).toBeInTheDocument();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("renders degraded calibration evidence without crashing or hiding replay clues", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        calibration_summary: {
          ...baseSimulationResult.calibration_summary,
          state: "degraded",
          state_reason: "Replay evidence is degraded because persisted route signals are incomplete.",
          degraded_request_count: 1,
          degraded_reasons: [{ reason: "missing_route_signals", count: 1 }],
        },
        changed_requests: [
          {
            ...baseSimulationResult.changed_requests[0],
            request_id: "req-degraded",
            baseline_route_mode: null,
            baseline_calibrated_routing: null,
            baseline_degraded_routing: null,
            baseline_route_score: null,
            simulated_route_mode: null,
            simulated_calibrated_routing: null,
            simulated_degraded_routing: null,
            simulated_route_score: null,
            baseline_route_target: "premium",
            simulated_route_target: "premium",
            baseline_route_reason: "token_complexity",
            simulated_route_reason: "token_complexity",
            baseline_terminal_status: "completed",
            simulated_terminal_status: "completed",
            baseline_policy_outcome: "outcome_evidence=sufficient(route_mode=calibrated)",
            simulated_policy_outcome: "outcome_evidence=degraded(route_mode=unscored reason=missing_route_signals)",
            baseline_estimated_cost: 0.1,
            simulated_estimated_cost: 0.1,
          },
        ],
      },
    });

    expect(screen.getByText(/Este borrador cambiaría 1 pedido de la muestra\./i)).toBeInTheDocument();
    expect(screen.getByText(/req-degraded/i)).toBeInTheDocument();
    expect(screen.getByText(/política outcome_evidence=sufficient\(route_mode=calibrated\) → outcome_evidence=degraded\(route_mode=unscored reason=missing_route_signals\)/i)).toBeInTheDocument();
    expect(screen.getByText(/paridad de ruteo: unscored → unscored/i)).toBeInTheDocument();
  });

  it("groups the runtime controls into sections and keeps the soft budget as advisory", () => {
    renderPolicyForm();

    const routing = screen.getByRole("heading", { name: "Ruteo" }).closest("section") as HTMLElement;
    expect(routing).toHaveTextContent("Objetivo de calidad");
    expect(routing).toHaveTextContent("Modo de ruteo");
    expect(routing).toHaveTextContent("Ruteo calibrado (heurística v0)");
    expect(routing).toHaveTextContent("Fallback a premium si falla el local");

    const limits = screen.getByRole("heading", { name: "Límites" }).closest("section") as HTMLElement;
    expect(limits).toHaveTextContent("Costo premium máximo por pedido (USD)");
    expect(limits).toHaveTextContent("Presupuesto duro acumulado (USD)");
    expect(limits).toHaveTextContent("Al agotarse el presupuesto");
    expect(limits).toHaveTextContent("Presupuesto blando (USD)");
    expect(limits).toHaveTextContent("Solo aviso: no bloquea ni degrada.");

    const cache = screen.getByRole("heading", { name: "Caché semántico" }).closest("section") as HTMLElement;
    expect(cache).toHaveTextContent("Caché semántico activado");
    expect(cache).toHaveTextContent("Umbral de similitud");
    expect(cache).toHaveTextContent("Antigüedad máxima (h)");

    expect(screen.getByRole("heading", { name: "Modelos premium permitidos" })).toBeInTheDocument();
    const evidence = screen.getByRole("heading", { name: "Evidencia" }).closest("section") as HTMLElement;
    expect(evidence).toHaveTextContent("Retención de evidencia");
    expect(evidence).toHaveTextContent("Minimización de metadatos");
  });

  it("offers strict metadata minimization", async () => {
    renderPolicyForm();
    await userEvent.selectOptions(screen.getByLabelText("Minimización de metadatos"), "strict");
    expect(screen.getByLabelText("Minimización de metadatos")).toHaveValue("strict");
    expect(screen.getByText("Estricta no guarda las señales de ruteo.")).toBeInTheDocument();
  });

  it("blocks save when cache tuning values are outside the enforced bounds", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
    await userEvent.type(screen.getByLabelText("Umbral de similitud"), "1.2");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    const message = await screen.findByText("El umbral de similitud tiene que estar entre 0 y 1.");
    // Shown next to the sticky Guardar button, where the operator is looking.
    expect(screen.getByRole("complementary", { name: "Vista previa" })).toContainElement(message);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("saves an edited routing quality target", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    const field = screen.getByLabelText("Objetivo de calidad");
    expect(field).toHaveValue("0.95");
    await userEvent.clear(field);
    await userEvent.type(field, "0.9");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ routing_quality_target: 0.9 });
  });

  it("saves a rate limit", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    const field = screen.getByLabelText("Límite de pedidos por minuto");
    expect(field).toHaveValue("");
    await userEvent.type(field, "120");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ rate_limit_requests_per_minute: 120 });

  });

  it("clears a rate limit back to unlimited", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave, policyOverrides: { rate_limit_requests_per_minute: 30 } });

    const field = screen.getByLabelText("Límite de pedidos por minuto");
    expect(field).toHaveValue("30");
    await userEvent.clear(field);
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ rate_limit_requests_per_minute: null });
  });

  it("blocks save when the rate limit is not a whole number between 1 and 100000", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    for (const value of ["0", "2.5", "100001", "abc"]) {
      await userEvent.clear(screen.getByLabelText("Límite de pedidos por minuto"));
      await userEvent.type(screen.getByLabelText("Límite de pedidos por minuto"), value);
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      expect(
        await screen.findByText("El límite tiene que ser un entero entre 1 y 100000 pedidos por minuto."),
      ).toBeInTheDocument();
    }
    expect(onSave).not.toHaveBeenCalled();
  });

  it("blocks save when the routing quality target is outside 0.5-1.0", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    for (const value of ["0.4", "1.01", "abc"]) {
      await userEvent.clear(screen.getByLabelText("Objetivo de calidad"));
      await userEvent.type(screen.getByLabelText("Objetivo de calidad"), value);
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(
        await screen.findByText("El objetivo de calidad tiene que estar entre 0.5 y 1."),
      ).toBeInTheDocument();
    }
    expect(onSave).not.toHaveBeenCalled();
  });

  it("does not preview a routing quality target outside 0.5-1.0", async () => {
    const onSimulate = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSimulate });

    await userEvent.clear(screen.getByLabelText("Objetivo de calidad"));
    await userEvent.type(screen.getByLabelText("Objetivo de calidad"), "0.2");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    expect(await screen.findByText("El objetivo de calidad tiene que estar entre 0.5 y 1.")).toBeInTheDocument();
    expect(onSimulate).not.toHaveBeenCalled();
  });

  it("hides the routing quality target when the runtime does not enforce it", () => {
    renderPolicyForm({ runtimeEnforcedFields: ["routing_mode_default", "allowed_premium_models"] });

    expect(screen.queryByLabelText("Objetivo de calidad")).not.toBeInTheDocument();
  });

  it("disables hard-budget enforcement selection until a hard limit is configured", async () => {
    renderPolicyForm();

    const enforcementSelect = screen.getByLabelText("Al agotarse el presupuesto");
    expect(enforcementSelect).toBeDisabled();
    expect(
      screen.getByText("Primero definir el presupuesto duro."),
    ).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Presupuesto duro acumulado (USD)"), "25");

    expect(screen.getByLabelText("Al agotarse el presupuesto")).toBeEnabled();
    expect(screen.queryByText("Primero definir el presupuesto duro.")).not.toBeInTheDocument();
  });
});
