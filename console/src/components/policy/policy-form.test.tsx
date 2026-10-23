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
  approximation_notes: [
    "Replay uses persisted ledger request metadata and route signals instead of raw prompt text.",
    "Rows without stored learned-router probabilities are replayed with the token-complexity heuristic.",
  ],
  approximation_note_codes: ["ledger_metadata_replay", "heuristic_fallback_rows"],
  window: {
    requested_from: null,
    requested_to: null,
    evaluated_from: "2026-03-27T00:00:00Z",
    evaluated_to: "2026-03-28T00:00:00Z",
    requested_limit: 50,
    changed_sample_limit: 5,
    returned_rows: 10,
  },
  summary: {
    evaluated_rows: 10,
    changed_routes: 1,
    newly_denied: 1,
    baseline_premium_cost: 0.2,
    simulated_premium_cost: 0.3,
    premium_cost_delta: 0.1,
    // One row served from the cache in the baseline; the draft denies a local one too.
    baseline_tier_counts: { local: 5, economy: 3, frontier: 1 },
    simulated_tier_counts: { local: 4, economy: 3, frontier: 1 },
    learned_router_rows: 7,
    heuristic_rows: 3,
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
      baseline_route_mode: "calibrated",
      simulated_route_mode: "degraded",
      baseline_calibrated_routing: true,
      simulated_calibrated_routing: false,
      baseline_degraded_routing: false,
      simulated_degraded_routing: true,
      baseline_route_score: 0.61,
      simulated_route_score: 0.31,
      baseline_estimated_cost: 0,
      simulated_estimated_cost: 0.1,
      baseline_tier: "local",
      simulated_tier: null,
      decision_source: "learned_router",
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

  it("keeps the capture flags the form does not show as they were stored", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave, policyOverrides: { prompt_capture_enabled: true, response_capture_enabled: true } });

    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ prompt_capture_enabled: true, response_capture_enabled: true });
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
    expect(preview.getByText(/ruta Local → Premium/)).toBeInTheDocument();
    expect(preview.getByText(/estado completado → denegado por política/)).toBeInTheDocument();
    expect(preview.getByText(/costo USD 0\.0000 → USD 0\.1000/)).toBeInTheDocument();
    expect(preview.getByRole("group", { name: "Δ costo premium" })).toHaveTextContent("USD 0.1000");
    expect(preview.getByText("paridad de ruteo: calibrado (puntaje 0.61) → degradado (puntaje 0.31)")).toBeInTheDocument();
    expect(preview.getByText("Comparado contra 10 pedidos recientes. No se guardó nada.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar política" })).toBeInTheDocument();
  });

  it("counts every changed request in the headline and lists the first five of them", () => {
    const row = baseSimulationResult.changed_requests[0];
    const changed = Array.from({ length: 7 }, (_, index) => ({ ...row, request_id: `req-${index + 1}` }));
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        window: { ...baseSimulationResult.window, changed_sample_limit: 50, returned_rows: 10 },
        summary: { ...baseSimulationResult.summary, changed_routes: 7, newly_denied: 0 },
        changed_requests: changed,
      },
    });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByText("Este borrador cambiaría 7 pedidos de la muestra.")).toBeInTheDocument();
    expect(preview.getByRole("heading", { name: "Pedidos que cambian · 5 de 7" })).toBeInTheDocument();
    expect(preview.getByText("req-5")).toBeInTheDocument();
    expect(preview.queryByText("req-6")).not.toBeInTheDocument();
  });

  it("says 'al menos' when the gateway cut the changed requests at the sample limit", () => {
    const row = baseSimulationResult.changed_requests[0];
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        // 41 rows evaluated, 19 routes change, but only 5 changed requests came back.
        window: { ...baseSimulationResult.window, changed_sample_limit: 5, returned_rows: 41 },
        summary: { ...baseSimulationResult.summary, evaluated_rows: 41, changed_routes: 19, newly_denied: 0 },
        changed_requests: Array.from({ length: 5 }, (_, index) => ({ ...row, request_id: `req-${index + 1}` })),
      },
    });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByText("Este borrador cambiaría al menos 19 pedidos de la muestra.")).toBeInTheDocument();
    expect(preview.queryByText("Este borrador cambiaría 5 pedidos de la muestra.")).not.toBeInTheDocument();
  });

  it("counts exactly when every evaluated row changed and the sample limit equals them", () => {
    const row = baseSimulationResult.changed_requests[0];
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        // 5 rows evaluated, all 5 changed, at most 5 returned: the sample is the whole window.
        window: { ...baseSimulationResult.window, changed_sample_limit: 5, returned_rows: 5 },
        summary: { ...baseSimulationResult.summary, evaluated_rows: 5, changed_routes: 5, newly_denied: 0 },
        changed_requests: Array.from({ length: 5 }, (_, index) => ({ ...row, request_id: `req-${index + 1}` })),
      },
    });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByText("Este borrador cambiaría 5 pedidos de la muestra.")).toBeInTheDocument();
    expect(preview.queryByText(/al menos/)).not.toBeInTheDocument();
  });

  it("leaves out the routing parity when the draft decides the row the same way", () => {
    const row = baseSimulationResult.changed_requests[0];
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        changed_requests: [
          {
            ...row,
            request_id: "req-same-parity",
            simulated_route_mode: row.baseline_route_mode,
            simulated_calibrated_routing: row.baseline_calibrated_routing,
            simulated_degraded_routing: row.baseline_degraded_routing,
            simulated_route_score: row.baseline_route_score,
            simulated_route_reason: row.baseline_route_reason,
          },
        ],
      },
    });

    const changed = within(screen.getByText("req-same-parity").closest("li") as HTMLElement);
    expect(changed.queryByText(/paridad de ruteo/)).not.toBeInTheDocument();
  });

  it("writes the policy outcome of a changed request in Spanish, never its raw text", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    const row = within(screen.getByText("req-1").closest("li") as HTMLElement);
    expect(row.getByText(/política Automático → Solo premium, denegado/)).toBeInTheDocument();
    expect(row.queryByText(/routing_mode|denied=|Request exceeds/)).not.toBeInTheDocument();
  });

  it("names only the routing mode and a denial of a policy outcome, and skips a change nobody can read", () => {
    const row = baseSimulationResult.changed_requests[0];
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        changed_requests: [
          {
            ...row,
            request_id: "req-mode",
            baseline_policy_outcome: "routing_mode=local_only;fallback=disabled;outcome_evidence=sufficient(route_mode=calibrated)",
            simulated_policy_outcome: "routing_mode=auto;soft_budget=exceeded",
          },
          {
            ...row,
            request_id: "req-noise",
            baseline_policy_outcome: "outcome_evidence=sufficient(route_mode=calibrated)",
            simulated_policy_outcome: "soft_budget=exceeded;budget_action=downgraded_to_local",
          },
        ],
      },
    });

    const mode = within(screen.getByText("req-mode").closest("li") as HTMLElement);
    expect(mode.getByText(/política Solo local → Automático/)).toBeInTheDocument();
    const noise = within(screen.getByText("req-noise").closest("li") as HTMLElement);
    expect(noise.queryByText(/(^|· )política /)).not.toBeInTheDocument();
    expect(screen.queryByText(/outcome_evidence|soft_budget|fallback=disabled/)).not.toBeInTheDocument();
  });

  it("writes the route of each changed request with the Spanish route labels, not the codes", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    const row = within(screen.getByText("req-1").closest("li") as HTMLElement);
    expect(row.getByText("Local")).toBeInTheDocument();
    expect(row.getByText("Premium")).toBeInTheDocument();
    expect(row.queryByText("local")).not.toBeInTheDocument();
    expect(row.queryByText(/policy_denied/)).not.toBeInTheDocument();
  });

  it("shows the tier counts before and after the draft for local, economy and frontier", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByRole("heading", { name: "Pedidos por nivel: actual → borrador" })).toBeInTheDocument();
    expect(preview.getByRole("group", { name: "local" })).toHaveTextContent("5 → 4");
    expect(preview.getByRole("group", { name: "economy" })).toHaveTextContent("3 → 3");
    expect(preview.getByRole("group", { name: "frontier" })).toHaveTextContent("1 → 1");
  });

  it("adds a 'Caché o denegado' row so each column of tier counts adds up to the evaluated rows", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByRole("group", { name: "Caché o denegado" })).toHaveTextContent("1 → 2");

    const evaluated = Number(preview.getByRole("group", { name: "Pedidos evaluados" }).textContent?.match(/\d+$/)?.[0]);
    expect(evaluated).toBe(10);
    const columns = [0, 0];
    for (const name of ["local", "economy", "frontier", "Caché o denegado"]) {
      const [before, after] = (preview.getByRole("group", { name }).textContent ?? "").match(/\d+/g)?.map(Number) ?? [];
      columns[0] += before;
      columns[1] += after;
    }
    expect(columns).toEqual([evaluated, evaluated]);
  });

  it("shows a zero remainder when every row has a tier", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        summary: {
          ...baseSimulationResult.summary,
          baseline_tier_counts: { local: 6, economy: 3, frontier: 1 },
          simulated_tier_counts: { local: 6, economy: 2, frontier: 2 },
        },
      },
    });

    expect(screen.getByRole("group", { name: "Caché o denegado" })).toHaveTextContent("0 → 0");
  });

  it("shows the preview of an older gateway that sends no tier counts and no note codes, without throwing", () => {
    // What a gateway from before the tier counts and the note codes answers.
    const { approximation_note_codes: _codes, ...withoutCodes } = baseSimulationResult;
    const { baseline_tier_counts: _baseline, simulated_tier_counts: _simulated, ...olderSummary } =
      baseSimulationResult.summary;
    renderPolicyForm({
      simulationResult: { ...withoutCodes, summary: olderSummary } as unknown as PolicySimulationResponse,
    });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByRole("group", { name: "Pedidos evaluados" })).toHaveTextContent("10");
    // No counts, no tier rows: nothing is made up.
    expect(preview.queryByRole("heading", { name: "Pedidos por nivel: actual → borrador" })).not.toBeInTheDocument();
    expect(preview.queryByRole("group", { name: "local" })).not.toBeInTheDocument();
    expect(preview.queryByRole("group", { name: "Caché o denegado" })).not.toBeInTheDocument();
    expect(preview.getByText("7 con el router aprendido · 3 con la heurística")).toBeInTheDocument();
    // Without codes, each note keeps the gateway's own text.
    expect(
      preview.getByText("Replay uses persisted ledger request metadata and route signals instead of raw prompt text."),
    ).toBeInTheDocument();
  });

  it("says how many rows the learned router re-decided and how many the heuristic did", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    expect(screen.getByText("7 con el router aprendido · 3 con la heurística")).toBeInTheDocument();
  });

  it.each([
    ["the learned router's count", ["learned_router_rows"]],
    ["the heuristic's count", ["heuristic_rows"]],
    ["both counts", ["learned_router_rows", "heuristic_rows"]],
  ] as const)("says nothing of the decision sources when an older gateway leaves out %s", (_name, absent) => {
    const summary = { ...baseSimulationResult.summary };
    for (const field of absent) {
      delete summary[field];
    }
    renderPolicyForm({ simulationResult: { ...baseSimulationResult, summary } });

    expect(screen.queryByText(/con el router aprendido|con la heurística/)).not.toBeInTheDocument();
    expect(screen.queryByText(/undefined|NaN/)).not.toBeInTheDocument();
    // The rest of the preview is still there.
    expect(screen.getByText("Pedidos evaluados")).toBeInTheDocument();
  });

  it.each([
    ["without cache rows", {}, "7 con el router aprendido · 3 con la heurística · 4 por la política"],
    [
      "before the cache clause",
      { cache_rows: 6 },
      "7 con el router aprendido · 3 con la heurística · 4 por la política · 6 siguen en caché",
    ],
  ])("adds the rows the policy decided %s", (_name, extra, text) => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        summary: { ...baseSimulationResult.summary, policy_rows: 4, ...extra },
      },
    });

    expect(screen.getByText(text)).toBeInTheDocument();
  });

  it.each([
    ["is zero", { policy_rows: 0 }],
    ["is absent", {}],
  ])("keeps the decision sources text as it was when the policy count %s", (_name, extra) => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        summary: { ...baseSimulationResult.summary, ...extra },
      },
    });

    expect(screen.getByText("7 con el router aprendido · 3 con la heurística")).toBeInTheDocument();
    expect(screen.queryByText(/por la política/)).not.toBeInTheDocument();
  });

  it("adds the cache hits the draft keeps, and their row reads the same before and after", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        summary: {
          ...baseSimulationResult.summary,
          evaluated_rows: 41,
          learned_router_rows: 35,
          heuristic_rows: 0,
          cache_rows: 6,
          baseline_tier_counts: { local: 29, economy: 0, frontier: 6 },
          simulated_tier_counts: { local: 19, economy: 0, frontier: 16 },
        },
      },
    });

    expect(screen.getByText("35 con el router aprendido · 0 con la heurística · 6 siguen en caché")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Caché o denegado" })).toHaveTextContent("6 → 6");
  });

  it("does not show tier counts for a window without rows", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        window: { ...baseSimulationResult.window, returned_rows: 0 },
        summary: {
          ...baseSimulationResult.summary,
          evaluated_rows: 0,
          changed_routes: 0,
          newly_denied: 0,
          premium_cost_delta: 0,
          baseline_tier_counts: { local: 0, economy: 0, frontier: 0 },
          simulated_tier_counts: { local: 0, economy: 0, frontier: 0 },
          learned_router_rows: 0,
          heuristic_rows: 0,
        },
        changed_requests: [],
      },
    });

    expect(screen.queryByRole("heading", { name: /Pedidos por nivel/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/con el router aprendido/)).not.toBeInTheDocument();
  });

  it("names the tier each changed request moves between", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        changed_requests: [
          {
            ...baseSimulationResult.changed_requests[0],
            request_id: "req-tier",
            baseline_route_target: "premium",
            simulated_route_target: "premium",
            baseline_terminal_status: "completed",
            simulated_terminal_status: "completed",
            baseline_tier: "economy",
            simulated_tier: "frontier",
          },
          baseSimulationResult.changed_requests[0],
        ],
      },
    });

    expect(within(screen.getByText("req-tier").closest("li") as HTMLElement).getByText(/nivel economy → frontier/)).toBeInTheDocument();
    expect(within(screen.getByText("req-1").closest("li") as HTMLElement).getByText(/nivel local → —/)).toBeInTheDocument();
  });

  it("words the approximation notes in Spanish by code", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    const notes = within(screen.getByText("Notas de la simulación").parentElement as HTMLElement);
    expect(notes.getByText("Se usan los metadatos guardados en el ledger, no el texto de los pedidos.")).toBeInTheDocument();
    expect(
      notes.getByText(
        "Los pedidos sin probabilidades guardadas, o que el borrador saca del router aprendido, usan la heurística.",
      ),
    ).toBeInTheDocument();
    expect(notes.queryByText(/Replay uses/)).not.toBeInTheDocument();
  });

  it("shows the raw text of an approximation note whose code it does not know", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        approximation_notes: ["A new kind of approximation.", "Replay uses persisted ledger request metadata."],
        approximation_note_codes: ["something_new", "ledger_metadata_replay"],
      },
    });

    expect(screen.getByText("A new kind of approximation.")).toBeInTheDocument();
    expect(screen.getByText("Se usan los metadatos guardados en el ledger, no el texto de los pedidos.")).toBeInTheDocument();
  });

  it("writes a premium cost that goes down with its sign after USD", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        summary: { ...baseSimulationResult.summary, premium_cost_delta: -0.05 },
      },
    });

    const preview = within(screen.getByRole("heading", { name: "Vista previa" }).closest("aside") as HTMLElement);
    expect(preview.getByRole("group", { name: "Δ costo premium" })).toHaveTextContent("USD −0.0500");
    expect(preview.getByText(/el gasto premium bajaría USD 0\.0500/)).toBeInTheDocument();
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
    // Both outcomes carry only evidence notes: nothing a reader could compare, and no raw text.
    expect(screen.queryByText(/outcome_evidence/)).not.toBeInTheDocument();
    expect(screen.queryByText(/(^|· )política /)).not.toBeInTheDocument();
    // Unscored on both sides is no difference to read: the parity clause is left out.
    expect(screen.queryByText(/paridad de ruteo/)).not.toBeInTheDocument();
  });

  it("writes the routing parity in Spanish for every state it can be in", () => {
    const row = baseSimulationResult.changed_requests[0];
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        changed_requests: [
          {
            ...row,
            request_id: "req-off",
            baseline_route_mode: "degraded",
            baseline_calibrated_routing: false,
            baseline_degraded_routing: true,
            baseline_route_score: 0.28,
            simulated_route_mode: null,
            simulated_calibrated_routing: null,
            simulated_degraded_routing: null,
            simulated_route_score: null,
            simulated_route_reason: "calibrated_routing_disabled",
          },
          {
            ...row,
            request_id: "req-partial",
            baseline_route_mode: null,
            baseline_calibrated_routing: true,
            baseline_degraded_routing: null,
            baseline_route_score: 0.4,
            simulated_route_mode: "something_new",
            simulated_calibrated_routing: null,
            simulated_degraded_routing: null,
            simulated_route_score: null,
          },
        ],
      },
    });

    expect(screen.getByText("paridad de ruteo: degradado (puntaje 0.28) → ruteo automático apagado")).toBeInTheDocument();
    expect(screen.getByText("paridad de ruteo: sin puntaje (calibrado, puntaje 0.40) → something_new")).toBeInTheDocument();
  });

  it("groups the runtime controls into sections and keeps the soft budget as advisory", () => {
    renderPolicyForm();

    const routing = screen.getByRole("heading", { name: "Ruteo" }).closest("section") as HTMLElement;
    expect(routing).toHaveTextContent("Objetivo de calidad");
    expect(routing).toHaveTextContent("Modo de ruteo");
    expect(routing).toHaveTextContent("Ruteo automático por nivel");
    expect(routing).not.toHaveTextContent("heurística v0");
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
    // The reason sits under the field; the sticky panel by Guardar names the field to fix.
    expect(screen.getByLabelText("Umbral de similitud").closest("div")).toContainElement(message);
    expect(screen.getByRole("complementary", { name: "Vista previa" })).toHaveTextContent(
      "Revisar los campos: Umbral de similitud.",
    );
    expect(onSave).not.toHaveBeenCalled();
  });

  it("links a field's hint and its error to the field for screen readers", async () => {
    renderPolicyForm();

    const threshold = screen.getByLabelText("Umbral de similitud");
    expect(threshold).toHaveAccessibleDescription("0 a 1, por cada búsqueda.");
    expect(threshold).not.toBeInvalid();

    await userEvent.clear(threshold);
    await userEvent.type(threshold, "1.2");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await screen.findByText("El umbral de similitud tiene que estar entre 0 y 1.");
    expect(threshold).toBeInvalid();
    expect(threshold).toHaveAccessibleDescription(
      /El umbral de similitud tiene que estar entre 0 y 1\..*0 a 1, por cada búsqueda\./,
    );
  });

  it("links the hint of a checkbox to it", () => {
    renderPolicyForm();

    expect(screen.getByRole("checkbox", { name: "Ruteo automático por nivel" })).toHaveAccessibleDescription(
      "Si se apaga, el tráfico automático va a local.",
    );
    expect(screen.getByLabelText("Límite de pedidos por minuto")).toHaveAccessibleDescription(
      "Sobre el límite el gateway responde 429 con Retry-After.",
    );
    expect(screen.getByLabelText("Al agotarse el presupuesto")).toHaveAccessibleDescription(
      "Primero definir el presupuesto duro.",
    );
  });

  it("clears a field's error as soon as it is edited, and the panel stops naming it", async () => {
    renderPolicyForm();

    const threshold = screen.getByLabelText("Umbral de similitud");
    await userEvent.clear(threshold);
    await userEvent.type(threshold, "1.2");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
    await screen.findByText("El umbral de similitud tiene que estar entre 0 y 1.");

    await userEvent.type(threshold, "0");

    expect(screen.queryByText("El umbral de similitud tiene que estar entre 0 y 1.")).not.toBeInTheDocument();
    expect(screen.queryByText(/Revisar los campos/)).not.toBeInTheDocument();
    expect(threshold).not.toBeInvalid();
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

  it("shows the quality target with two decimals and a hint with the console's range", () => {
    renderPolicyForm({ policyOverrides: { routing_quality_target: 0.9 } });

    const field = screen.getByLabelText("Objetivo de calidad");
    expect(field).toHaveValue("0.90");
    expect(field).toHaveAccessibleDescription(/0\.75 a 1\.00/);
    expect(screen.queryByText(/0\.5 a 1\.0/)).not.toBeInTheDocument();
  });

  it("shows a stored target below the console's range as it is and blocks saving it", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave, policyOverrides: { routing_quality_target: 0.6 } });

    expect(screen.getByLabelText("Objetivo de calidad")).toHaveValue("0.60");

    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    expect(await screen.findByText("El objetivo de calidad tiene que estar entre 0.75 y 1.00.")).toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("keeps a stored target finer than a hundredth while the field is not edited", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave, policyOverrides: { routing_quality_target: 0.7544 } });

    expect(screen.getByLabelText("Objetivo de calidad")).toHaveValue("0.75");
    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ routing_quality_target: 0.7544, fallback_enabled: false });
  });

  it("writes the target the operator types over a finer stored one", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave, policyOverrides: { routing_quality_target: 0.7544 } });

    await userEvent.clear(screen.getByLabelText("Objetivo de calidad"));
    await userEvent.type(screen.getByLabelText("Objetivo de calidad"), "0,8");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ routing_quality_target: 0.8 });
  });

  it("does not count retyping a number the same way as a change", async () => {
    renderPolicyForm({ policyOverrides: { routing_quality_target: 0.9 } });

    const field = screen.getByLabelText("Objetivo de calidad");
    expect(field).toHaveValue("0.90");
    await userEvent.clear(field);
    await userEvent.type(field, "0.9");

    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar política" })).toBeDisabled();

    await userEvent.type(field, "1");
    expect(screen.getByText("Cambios sin guardar")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar política" })).toBeEnabled();
  });

  it("says 'Sin límite' in every optional limit that is empty", () => {
    renderPolicyForm();

    for (const label of [
      "Límite de pedidos por minuto",
      "Costo premium máximo por pedido (USD)",
      "Presupuesto duro acumulado (USD)",
      "Presupuesto blando (USD)",
    ]) {
      expect(screen.getByLabelText(label), label).toHaveAttribute("placeholder", "Sin límite");
    }
    // The placeholder says it; a hint repeating it would be one more line to read.
    expect(screen.queryByText("Vacío: sin límite.")).not.toBeInTheDocument();
  });

  it("does not validate a field the runtime does not enforce, and keeps it as it was stored", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({
      onSave,
      runtimeEnforcedFields: ["routing_mode_default", "fallback_enabled", "allowed_premium_models"],
      policyOverrides: { routing_quality_target: 0.6 },
    });

    expect(screen.queryByLabelText("Objetivo de calidad")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ routing_quality_target: 0.6, fallback_enabled: false });
    expect(screen.queryByText(/Revisar los campos/)).not.toBeInTheDocument();
  });

  it("reads a decimal comma in the quality target", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    await userEvent.clear(screen.getByLabelText("Objetivo de calidad"));
    await userEvent.type(screen.getByLabelText("Objetivo de calidad"), "0,85");
    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toMatchObject({ routing_quality_target: 0.85 });
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

    for (const value of ["0", "2.5", "10,5", "100001"]) {
      await userEvent.clear(screen.getByLabelText("Límite de pedidos por minuto"));
      await userEvent.type(screen.getByLabelText("Límite de pedidos por minuto"), value);
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      expect(
        await screen.findByText("El límite tiene que ser un entero entre 1 y 100000 pedidos por minuto."),
      ).toBeInTheDocument();
    }
    expect(onSave).not.toHaveBeenCalled();
  });

  it("blocks save when the routing quality target is outside 0.75-1.00", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    for (const value of ["0.4", "0.7", "1.01"]) {
      await userEvent.clear(screen.getByLabelText("Objetivo de calidad"));
      await userEvent.type(screen.getByLabelText("Objetivo de calidad"), value);
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(
        await screen.findByText("El objetivo de calidad tiene que estar entre 0.75 y 1.00."),
      ).toBeInTheDocument();
    }
    expect(onSave).not.toHaveBeenCalled();
  });

  it("does not preview a routing quality target outside 0.75-1.00", async () => {
    const onSimulate = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSimulate });

    await userEvent.clear(screen.getByLabelText("Objetivo de calidad"));
    await userEvent.type(screen.getByLabelText("Objetivo de calidad"), "0.2");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    expect(await screen.findByText("El objetivo de calidad tiene que estar entre 0.75 y 1.00.")).toBeInTheDocument();
    expect(onSimulate).not.toHaveBeenCalled();
  });

  describe("numeric fields", () => {
    const usdFields = [
      ["Costo premium máximo por pedido (USD)", "max_premium_cost_per_request"],
      ["Presupuesto duro acumulado (USD)", "hard_budget_limit_usd"],
      ["Presupuesto blando (USD)", "soft_budget_usd"],
    ] as const;

    it.each(usdFields)("%s reads a decimal comma and surrounding spaces", async (label, key) => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSave });

      await userEvent.type(screen.getByLabelText(label), "10,5");
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
      expect(onSave.mock.calls[0][0]).toMatchObject({ [key]: 10.5 });

      await userEvent.clear(screen.getByLabelText(label));
      await userEvent.type(screen.getByLabelText(label), " 3 ");
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await waitFor(() => expect(onSave).toHaveBeenCalledTimes(2));
      expect(onSave.mock.calls[1][0]).toMatchObject({ [key]: 3 });
    });

    it.each(usdFields)("%s means no limit only when it is empty, never for a typo", async (label, key) => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({
        onSave,
        policyOverrides: { [key]: 5, ...(key === "hard_budget_limit_usd" ? { hard_budget_enforcement: "deny" } : {}) },
      });

      await userEvent.clear(screen.getByLabelText(label));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
      expect(onSave.mock.calls[0][0]).toMatchObject({ [key]: null });

      await userEvent.type(screen.getByLabelText(label), "abc");
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(await screen.findByText("Número inválido.")).toBeInTheDocument();
      expect(screen.getByLabelText(label)).toBeInvalid();
      expect(onSave).toHaveBeenCalledTimes(1);
    });

    it("reads a rate limit with spaces, and blank as unlimited", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSave });

      await userEvent.type(screen.getByLabelText("Límite de pedidos por minuto"), " 3 ");
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
      expect(onSave.mock.calls[0][0]).toMatchObject({ rate_limit_requests_per_minute: 3 });
    });

    it("calls a typo in the rate limit an invalid number, not an out-of-range one", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSave });

      await userEvent.type(screen.getByLabelText("Límite de pedidos por minuto"), "abc");
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(await screen.findByText("Número inválido.")).toBeInTheDocument();
      expect(onSave).not.toHaveBeenCalled();
    });

    it("reads a decimal comma in the cache threshold", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSave });

      await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
      await userEvent.type(screen.getByLabelText("Umbral de similitud"), "0,82");
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
      expect(onSave.mock.calls[0][0]).toMatchObject({ semantic_cache_similarity_threshold: 0.82 });
    });

    it("never saves an emptied cache threshold as 0", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSave });

      await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(await screen.findByText("El umbral de similitud tiene que estar entre 0 y 1.")).toBeInTheDocument();
      expect(onSave).not.toHaveBeenCalled();
    });

    it("blocks simulate with the same errors as save, the rate limit included", async () => {
      const onSimulate = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSimulate });

      await userEvent.type(screen.getByLabelText("Límite de pedidos por minuto"), "0");
      await userEvent.type(screen.getByLabelText("Presupuesto blando (USD)"), "abc");
      await userEvent.click(screen.getByRole("button", { name: "Simular" }));

      expect(
        await screen.findByText("El límite tiene que ser un entero entre 1 y 100000 pedidos por minuto."),
      ).toBeInTheDocument();
      expect(screen.getByText("Número inválido.")).toBeInTheDocument();
      expect(screen.getByRole("complementary", { name: "Vista previa" })).toHaveTextContent(
        "Revisar los campos: Límite de pedidos por minuto, Presupuesto blando (USD).",
      );
      expect(onSimulate).not.toHaveBeenCalled();
    });

    it("links the missing-model error to the field that adds one", async () => {
      renderPolicyForm();

      await userEvent.click(screen.getByRole("button", { name: "Quitar openai/gpt-4o-mini" }));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      await screen.findByText("Elegir al menos un modelo premium.");
      const input = screen.getByRole("textbox", { name: "Agregar modelo" });
      expect(input).toBeInvalid();
      expect(input).toHaveAccessibleDescription("Elegir al menos un modelo premium.");

      await userEvent.click(screen.getByRole("button", { name: "openai/gpt-4o-mini" }));
      expect(screen.queryByText("Elegir al menos un modelo premium.")).not.toBeInTheDocument();
      expect(input).not.toBeInvalid();
    });

    it("blocks simulate without a premium model", async () => {
      const onSimulate = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSimulate });

      await userEvent.click(screen.getByRole("button", { name: "Quitar openai/gpt-4o-mini" }));
      await userEvent.click(screen.getByRole("button", { name: "Simular" }));

      expect(await screen.findByText("Elegir al menos un modelo premium.")).toBeInTheDocument();
      expect(onSimulate).not.toHaveBeenCalled();
    });
  });

  it("writes the routing modes in Spanish and keeps their codes as values", () => {
    renderPolicyForm();

    const options = within(screen.getByLabelText("Modo de ruteo")).getAllByRole("option");
    expect(options.map((option) => option.textContent)).toEqual(["Automático", "Solo local", "Solo premium"]);
    expect(options.map((option) => option.getAttribute("value"))).toEqual(["auto", "local_only", "premium_only"]);
  });

  describe("saving", () => {
    it("confirms with 'Política guardada.' once the save succeeds, until the next edit", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      renderPolicyForm({ onSave });

      await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
      expect(screen.queryByText("Política guardada.")).not.toBeInTheDocument();
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(await screen.findByRole("status")).toHaveTextContent("Política guardada.");

      await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
      expect(screen.queryByText("Política guardada.")).not.toBeInTheDocument();
    });

    it("does not confirm a save that failed and shows why", async () => {
      const onSave = vi.fn().mockRejectedValue(new Error("El gateway devolvió un error (500)."));
      renderPolicyForm({ onSave });

      await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(await screen.findByText("El gateway devolvió un error (500).")).toBeInTheDocument();
      expect(screen.queryByText("Política guardada.")).not.toBeInTheDocument();
    });

    it("takes the confirmation away when the draft is discarded", async () => {
      renderPolicyForm();

      await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await screen.findByText("Política guardada.");
      // The harness keeps the stored policy as it was, so the draft is still a change to discard.
      await userEvent.click(screen.getByRole("button", { name: "Descartar cambios" }));

      expect(screen.queryByText("Política guardada.")).not.toBeInTheDocument();
      expect(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" })).toBeChecked();
    });

    it("takes the field errors away when the draft is discarded", async () => {
      renderPolicyForm();

      await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
      await userEvent.type(screen.getByLabelText("Umbral de similitud"), "1.2");
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await screen.findByText("El umbral de similitud tiene que estar entre 0 y 1.");

      await userEvent.click(screen.getByRole("button", { name: "Descartar cambios" }));

      expect(screen.queryByText("El umbral de similitud tiene que estar entre 0 y 1.")).not.toBeInTheDocument();
      expect(screen.queryByText(/Revisar los campos/)).not.toBeInTheDocument();
      expect(screen.getByLabelText("Umbral de similitud")).toHaveValue("0.9");
      expect(screen.getByLabelText("Umbral de similitud")).not.toBeInvalid();
    });

    it("clears a failed save's error when the operator tries again", async () => {
      const onSave = vi
        .fn()
        .mockRejectedValueOnce(new Error("El gateway devolvió un error (500)."))
        .mockResolvedValue(undefined);
      renderPolicyForm({ onSave });

      await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await screen.findByText("El gateway devolvió un error (500).");

      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

      expect(await screen.findByText("Política guardada.")).toBeInTheDocument();
      expect(screen.queryByText("El gateway devolvió un error (500).")).not.toBeInTheDocument();
    });

    it("clears a failed save's error when the next check finds a field to fix", async () => {
      const onSave = vi.fn().mockRejectedValue(new Error("El gateway devolvió un error (500)."));
      renderPolicyForm({ onSave });

      await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await screen.findByText("El gateway devolvió un error (500).");

      await userEvent.type(screen.getByLabelText("Límite de pedidos por minuto"), "abc");
      await userEvent.click(screen.getByRole("button", { name: "Simular" }));

      expect(await screen.findByText("Número inválido.")).toBeInTheDocument();
      expect(screen.queryByText("El gateway devolvió un error (500).")).not.toBeInTheDocument();
    });

    it("stops confirming when a model is added, not only when a field is typed in", async () => {
      renderPolicyForm();

      await userEvent.click(screen.getByRole("checkbox", { name: "Fallback a premium si falla el local" }));
      await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));
      await screen.findByText("Política guardada.");

      await userEvent.click(screen.getByRole("button", { name: "openai/gpt-4.1-mini" }));
      expect(screen.queryByText("Política guardada.")).not.toBeInTheDocument();
    });
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
