import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import EvaluationPage from "@/app/(console)/evaluacion/page";
import type { TenantPolicy } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";
import { routerReplayFixture } from "@/test/router-replay-fixture";

const adminApi = vi.hoisted(() => ({
  getRouterEvaluation: vi.fn(),
  listTenants: vi.fn(),
  getTenantPolicy: vi.fn(),
  updateTenantPolicy: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    getRouterEvaluation: adminApi.getRouterEvaluation,
    listTenants: adminApi.listTenants,
    getTenantPolicy: adminApi.getTenantPolicy,
    updateTenantPolicy: adminApi.updateTenantPolicy,
  };
});

const policy: TenantPolicy = {
  routing_mode_default: "auto",
  calibrated_routing_enabled: true,
  allowed_premium_models: ["openai/gpt-4.1"],
  semantic_cache_enabled: true,
  semantic_cache_similarity_threshold: 0.9,
  semantic_cache_max_entry_age_hours: 168,
  fallback_enabled: true,
  max_premium_cost_per_request: null,
  hard_budget_limit_usd: null,
  hard_budget_enforcement: null,
  soft_budget_usd: null,
  prompt_capture_enabled: false,
  response_capture_enabled: false,
  evidence_retention_window: "30d",
  metadata_minimization_level: "standard",
  routing_quality_target: 0.95,
};

const tenants = [
  {
    id: "default",
    name: "Default Workspace",
    description: null,
    metadata: {},
    active: true,
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
];

function costCard() {
  return screen.getByRole("group", { name: "Costo por 1000 prompts" });
}

describe("evaluation page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Keep the replay feed paused so tests stay deterministic.
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("reduce"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })) as unknown as typeof window.matchMedia;
    adminApi.listTenants.mockResolvedValue(tenants);
    adminApi.getRouterEvaluation.mockResolvedValue(routerReplayFixture);
  });

  it("shows the nested held-out figures and per-model latency in the header", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const header = await screen.findByRole("region", { name: "Cifra anidada" });
    expect(within(header).getByText("−31 %")).toBeInTheDocument();
    expect(within(header).getByText("IC 95 % [28 %, 35 %]")).toBeInTheDocument();
    expect(within(header).getByText("−17 %")).toBeInTheDocument();
    expect(within(header).getByText("IC 95 % [12 %, 21 %]")).toBeInTheDocument();
    expect(within(header).getByText("qwen2.5:7b")).toBeInTheDocument();
    expect(within(header).getByText("21.3 s")).toBeInTheDocument();
  });

  it("updates the cost card when the slider moves", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    expect(slider).toHaveValue("0.95");
    expect(within(costCard()).getByText("$2.500")).toBeInTheDocument();

    fireEvent.change(slider, { target: { value: "0.75" } });
    expect(within(costCard()).getByText("$1.500")).toBeInTheDocument();

    fireEvent.change(slider, { target: { value: "1" } });
    expect(within(costCard()).getByText("$4.000")).toBeInTheDocument();
    expect(screen.getByText("Punto elegido: todo frontier (τ_local = ∞, τ_economy = ∞)")).toBeInTheDocument();
  });

  it("shows savings against all-frontier and random at the same quality", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    fireEvent.change(slider, { target: { value: "0.75" } });
    // cost 1.5 vs frontier 4.0 → −62.5 %; random at 0.75 = all-economy 2.0 → −25 %.
    expect(within(screen.getByRole("group", { name: "Ahorro vs todo frontier" })).getByText("−63 %")).toBeInTheDocument();
    expect(within(screen.getByRole("group", { name: "Ahorro vs mezcla aleatoria" })).getByText("−25 %")).toBeInTheDocument();
  });

  it("applies the target to the selected tenant with the rest of its policy intact", async () => {
    const user = userEvent.setup();
    adminApi.getTenantPolicy.mockResolvedValue(policy);
    adminApi.updateTenantPolicy.mockResolvedValue({ ...policy, routing_quality_target: 0.9 });
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    fireEvent.change(slider, { target: { value: "0.9" } });
    await screen.findByRole("option", { name: "Default Workspace" });
    await user.click(screen.getByRole("button", { name: "Aplicar a este tenant" }));

    await waitFor(() =>
      expect(adminApi.updateTenantPolicy).toHaveBeenCalledWith("nebula-admin-key", "default", {
        ...policy,
        routing_quality_target: 0.9,
      }),
    );
    expect(
      await screen.findByText("Guardado: routing_quality_target = 0.900 en Default Workspace"),
    ).toBeInTheDocument();
  });

  it("does not write when the tenant policy cannot be read", async () => {
    const user = userEvent.setup();
    adminApi.getTenantPolicy.mockRejectedValue(new Error("Tenant policy unavailable."));
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    await screen.findByRole("option", { name: "Default Workspace" });
    await user.click(await screen.findByRole("button", { name: "Aplicar a este tenant" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Tenant policy unavailable.");
    expect(adminApi.updateTenantPolicy).not.toHaveBeenCalled();
  });

  it("shows an empty state when the gateway has no replay", async () => {
    adminApi.getRouterEvaluation.mockResolvedValue(null);
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByText("No hay replay del router")).toBeInTheDocument();
    expect(screen.getByText(/python -m scripts\.router\.train/)).toBeInTheDocument();
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });

  it("credits the corpus sources in a footnote", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const note = await screen.findByText(/Dolly/);
    expect(note).toHaveTextContent("CC BY-SA 3.0");
    expect(note).toHaveTextContent("GSM8K");
    expect(note).toHaveTextContent("MBPP");
  });
});
