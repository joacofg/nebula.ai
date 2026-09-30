import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import PolicyPage from "@/app/(console)/policy/page";
import * as adminApi from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    listTenants: vi.fn(),
    getTenantPolicy: vi.fn(),
    getPolicyOptions: vi.fn(),
    updateTenantPolicy: vi.fn(),
    simulateTenantPolicy: vi.fn(),
  };
});

const listTenantsMock = vi.mocked(adminApi.listTenants);
const getTenantPolicyMock = vi.mocked(adminApi.getTenantPolicy);
const getPolicyOptionsMock = vi.mocked(adminApi.getPolicyOptions);
const updateTenantPolicyMock = vi.mocked(adminApi.updateTenantPolicy);
const simulateTenantPolicyMock = vi.mocked(adminApi.simulateTenantPolicy);

function renderPolicyPage() {
  return renderWithProviders(<PolicyPage />, { adminKey: "admin-key" });
}

beforeEach(() => {
  vi.clearAllMocks();

  listTenantsMock.mockResolvedValue([
    {
      id: "tenant-a",
      name: "Tenant A",
      description: null,
      metadata: {},
      active: true,
      created_at: "2026-03-27T00:00:00Z",
      updated_at: "2026-03-27T00:00:00Z",
    },
    {
      id: "tenant-b",
      name: "Tenant B",
      description: null,
      metadata: {},
      active: true,
      created_at: "2026-03-28T00:00:00Z",
      updated_at: "2026-03-28T00:00:00Z",
    },
  ]);
  getTenantPolicyMock.mockImplementation(async (_adminKey, tenantId) => ({
    routing_mode_default: tenantId === "tenant-b" ? "local_only" : "auto",
    calibrated_routing_enabled: true,
    fallback_enabled: tenantId === "tenant-b" ? false : true,
    semantic_cache_enabled: true,
    semantic_cache_similarity_threshold: tenantId === "tenant-b" ? 0.88 : 0.9,
    semantic_cache_max_entry_age_hours: tenantId === "tenant-b" ? 72 : 168,
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
  }));
  getPolicyOptionsMock.mockResolvedValue({
    routing_modes: ["auto", "local_only", "premium_only"],
    known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
    default_premium_model: "openai/gpt-4o-mini",
    runtime_enforced_fields: [
      "routing_quality_target",
      "rate_limit_requests_per_minute",
      "routing_mode_default",
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
  });
  updateTenantPolicyMock.mockResolvedValue({
    routing_mode_default: "premium_only",
    calibrated_routing_enabled: false,
    fallback_enabled: true,
    semantic_cache_enabled: true,
    semantic_cache_similarity_threshold: 0.82,
    semantic_cache_max_entry_age_hours: 48,
    allowed_premium_models: ["openai/gpt-4o-mini"],
    max_premium_cost_per_request: null,
    hard_budget_limit_usd: 20,
    hard_budget_enforcement: "downgrade",
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
    evidence_retention_window: "30d",
    metadata_minimization_level: "standard",
    routing_quality_target: 0.95,
  });
  simulateTenantPolicyMock.mockResolvedValue({
    tenant_id: "tenant-a",
    candidate_policy: {
      routing_mode_default: "premium_only",
      calibrated_routing_enabled: false,
      fallback_enabled: true,
      semantic_cache_enabled: true,
      semantic_cache_similarity_threshold: 0.82,
      semantic_cache_max_entry_age_hours: 48,
      allowed_premium_models: ["openai/gpt-4o-mini"],
      max_premium_cost_per_request: null,
      hard_budget_limit_usd: 20,
      hard_budget_enforcement: "downgrade",
      soft_budget_usd: null,
      prompt_capture_enabled: false,
      response_capture_enabled: false,
      evidence_retention_window: "30d",
      metadata_minimization_level: "standard",
      routing_quality_target: 0.95,
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
    approximation_notes: ["Replay uses stored route signals."],
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
      newly_denied: 0,
      baseline_premium_cost: 0,
      simulated_premium_cost: 0.01,
      premium_cost_delta: 0.01,
    },
    changed_requests: [
      {
        request_id: "req-1",
        timestamp: "2026-03-27T12:00:00Z",
        requested_model: "nebula-auto",
        baseline_route_target: "local",
        simulated_route_target: "premium",
        baseline_terminal_status: "completed",
        simulated_terminal_status: "completed",
        baseline_policy_outcome: "default",
        simulated_policy_outcome: "routing_mode=premium_only",
        baseline_route_reason: "token_complexity",
        simulated_route_reason: "token_complexity",
        baseline_route_mode: "calibrated",
        simulated_route_mode: "degraded",
        baseline_calibrated_routing: true,
        simulated_calibrated_routing: false,
        baseline_degraded_routing: false,
        simulated_degraded_routing: true,
        baseline_route_score: 0.74,
        simulated_route_score: 0.31,
        baseline_estimated_cost: 0,
        simulated_estimated_cost: 0.01,
      },
      {
        request_id: "req-2",
        timestamp: "2026-03-27T13:00:00Z",
        requested_model: "nebula-auto",
        baseline_route_target: "local",
        simulated_route_target: "local",
        baseline_terminal_status: "completed",
        simulated_terminal_status: "completed",
        baseline_policy_outcome: "default",
        simulated_policy_outcome: "default",
        baseline_route_reason: "token_complexity",
        simulated_route_reason: "calibrated_routing_disabled",
        baseline_route_mode: "degraded",
        simulated_route_mode: null,
        baseline_calibrated_routing: false,
        simulated_calibrated_routing: null,
        baseline_degraded_routing: true,
        simulated_degraded_routing: null,
        baseline_route_score: 0.28,
        simulated_route_score: null,
        baseline_estimated_cost: 0,
        simulated_estimated_cost: 0,
      },
    ],
  });
});

describe("policy-page", () => {
  it("renders grouped policy sections", async () => {
    renderPolicyPage();

    expect(await screen.findByRole("heading", { name: "Ruteo" })).toBeInTheDocument();
    expect(screen.getByLabelText("Umbral de similitud")).toBeInTheDocument();
    expect(screen.getByLabelText("Antigüedad máxima (h)")).toBeInTheDocument();
    expect(screen.getByLabelText("Presupuesto blando (USD)")).toBeInTheDocument();
    expect(screen.getByLabelText("Retención de evidencia")).toBeInTheDocument();
    expect(screen.getByLabelText("Minimización de metadatos")).toBeInTheDocument();
    expect(screen.queryByLabelText("Prompt capture enabled")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Response capture enabled")).not.toBeInTheDocument();
  });

  it("previews the current draft without saving and keeps save explicit", async () => {
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Vista previa" });
    await userEvent.selectOptions(screen.getByLabelText("Modo de ruteo"), "premium_only");
    await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
    await userEvent.type(screen.getByLabelText("Umbral de similitud"), "0.82");
    await userEvent.clear(screen.getByLabelText("Antigüedad máxima (h)"));
    await userEvent.type(screen.getByLabelText("Antigüedad máxima (h)"), "48");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    await waitFor(() => {
      expect(simulateTenantPolicyMock).toHaveBeenCalledWith(
        "admin-key",
        "tenant-a",
        expect.objectContaining({
          candidate_policy: expect.objectContaining({
            routing_mode_default: "premium_only",
            semantic_cache_similarity_threshold: 0.82,
            semantic_cache_max_entry_age_hours: 48,
          }),
          limit: 50,
          changed_sample_limit: 5,
        }),
      );
    });

    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
    expect(await screen.findByText("Pedidos que cambian")).toBeInTheDocument();
    expect(screen.getByText(/Comparado contra 2 pedidos recientes\./i)).toBeInTheDocument();
    expect(screen.getByText(/No se guardó nada\./i)).toBeInTheDocument();
    expect(
      screen.getByText(
        "paridad de ruteo: calibrated (calibrated, score 0.74) → degraded (degraded, score 0.31)",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("paridad de ruteo: degraded (degraded, score 0.28) → rollout disabled"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("shows preview errors from the simulation mutation", async () => {
    simulateTenantPolicyMock.mockRejectedValueOnce(new Error("from_timestamp must be less than or equal to to_timestamp."));
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Vista previa" });
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    expect(
      await screen.findByText(
        "La simulación falló: from_timestamp must be less than or equal to to_timestamp.",
      ),
    ).toBeInTheDocument();
    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("shows explicit zero-result preview state", async () => {
    simulateTenantPolicyMock.mockResolvedValueOnce({
      tenant_id: "tenant-a",
      candidate_policy: {
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
      approximation_notes: [],
      window: {
        requested_from: null,
        requested_to: null,
        evaluated_from: null,
        evaluated_to: null,
        requested_limit: 50,
        changed_sample_limit: 5,
        returned_rows: 0,
      },
      summary: {
        evaluated_rows: 0,
        changed_routes: 0,
        newly_denied: 0,
        baseline_premium_cost: 0,
        simulated_premium_cost: 0,
        premium_cost_delta: 0,
      },
      changed_requests: [],
    });

    renderPolicyPage();

    await screen.findByRole("heading", { name: "Vista previa" });
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    expect(
      await screen.findByText("No hubo tráfico reciente en la ventana de la simulación."),
    ).toBeInTheDocument();
    expect(screen.getByText(/No se guardó nada\./i)).toBeInTheDocument();
    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("keeps unchanged previews explicitly non-saving", async () => {
    simulateTenantPolicyMock.mockResolvedValueOnce({
      tenant_id: "tenant-a",
      candidate_policy: {
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
      approximation_notes: [],
      window: {
        requested_from: null,
        requested_to: null,
        evaluated_from: "2026-03-27T00:00:00Z",
        evaluated_to: "2026-03-28T00:00:00Z",
        requested_limit: 50,
        changed_sample_limit: 5,
        returned_rows: 3,
      },
      summary: {
        evaluated_rows: 3,
        changed_routes: 0,
        newly_denied: 0,
        baseline_premium_cost: 0,
        simulated_premium_cost: 0,
        premium_cost_delta: 0,
      },
      changed_requests: [],
    });

    renderPolicyPage();

    await screen.findByRole("heading", { name: "Vista previa" });
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    expect(await screen.findByText("Sin cambios")).toBeInTheDocument();
    expect(screen.getByText("El borrador no cambia los pedidos de la muestra.")).toBeInTheDocument();
    expect(screen.getByText(/No se guardó nada\./i)).toBeInTheDocument();
    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
  });

  it("clears stale preview evidence after a successful save", async () => {
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Vista previa" });
    await userEvent.selectOptions(screen.getByLabelText("Modo de ruteo"), "premium_only");
    await userEvent.clear(screen.getByLabelText("Umbral de similitud"));
    await userEvent.type(screen.getByLabelText("Umbral de similitud"), "0.82");
    await userEvent.clear(screen.getByLabelText("Antigüedad máxima (h)"));
    await userEvent.type(screen.getByLabelText("Antigüedad máxima (h)"), "48");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    expect(await screen.findByText("Pedidos que cambian")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Guardar política" }));

    await waitFor(() => {
      expect(updateTenantPolicyMock).toHaveBeenCalledWith(
        "admin-key",
        "tenant-a",
        expect.objectContaining({
          routing_mode_default: "premium_only",
          semantic_cache_similarity_threshold: 0.82,
          semantic_cache_max_entry_age_hours: 48,
        }),
      );
    });

    await waitFor(() => {
      expect(screen.queryByText("Pedidos que cambian")).not.toBeInTheDocument();
    });
    expect(
      screen.getByText("Simular para comparar el borrador con el tráfico reciente antes de guardar."),
    ).toBeInTheDocument();
  });

  it("clears stale preview evidence when switching tenants", async () => {
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Vista previa" });
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));

    expect(await screen.findByText("Pedidos que cambian")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Tenant"), "tenant-b");

    await waitFor(() => {
      expect(getTenantPolicyMock).toHaveBeenCalledWith("admin-key", "tenant-b");
    });
    await waitFor(() => {
      expect(screen.queryByText("Pedidos que cambian")).not.toBeInTheDocument();
    });
    expect(
      screen.getByText("Simular para comparar el borrador con el tráfico reciente antes de guardar."),
    ).toBeInTheDocument();
    expect(screen.getByRole("form", { name: "Política de Tenant B" })).toBeInTheDocument();
  });
});
