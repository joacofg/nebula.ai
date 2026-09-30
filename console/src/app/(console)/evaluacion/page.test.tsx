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

function readout(name: string) {
  return screen.getByRole("group", { name });
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

  it("titles the page and states the corpus in the header cells", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByRole("heading", { level: 1, name: "Evaluación del router" })).toBeInTheDocument();
    expect(screen.getByText("v1 · 3 niveles")).toBeInTheDocument();
    expect(await screen.findByText("4 pedidos")).toBeInTheDocument();
    expect(screen.getByText("Sin red ni Ollama")).toBeInTheDocument();
  });

  it("lists the nested held-out figures and per-model latency as a characteristics table", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const table = await screen.findByRole("table", { name: "Características a calidad objetivo 0.95" });
    const saving = within(table).getByRole("row", { name: /Ahorro vs todo frontier/ });
    expect(saving).toHaveTextContent("31 %");
    expect(saving).toHaveTextContent("28–35 %");
    const random = within(table).getByRole("row", { name: /Ahorro vs mezcla aleatoria/ });
    expect(random).toHaveTextContent("17 %");
    expect(random).toHaveTextContent("12–21 %");
    expect(within(table).getByRole("row", { name: /qwen2\.5:7b · n = 30/ })).toHaveTextContent("21.3 s");
    expect(within(table).getByRole("row", { name: /Costo/ })).toHaveTextContent("USD 1.70");
  });

  it("updates the cost readout when the slider moves", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    expect(slider).toHaveValue("0.95");
    expect(readout("Costo por 1000 pedidos")).toHaveTextContent("USD 2.50");

    fireEvent.change(slider, { target: { value: "0.75" } });
    expect(readout("Costo por 1000 pedidos")).toHaveTextContent("USD 1.50");

    fireEvent.change(slider, { target: { value: "1" } });
    expect(readout("Costo por 1000 pedidos")).toHaveTextContent("USD 4.00");
    expect(readout("Umbrales τ local · economy")).toHaveTextContent("todo frontier");
  });

  it("shows savings against all-frontier and random at the same quality", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    fireEvent.change(slider, { target: { value: "0.75" } });
    // cost 1.5 vs frontier 4.0 → 62.5 % saving; random at 0.75 = all-economy 2.0 → 25 %.
    expect(readout("Ahorro vs todo frontier")).toHaveTextContent("63 %");
    expect(readout("Ahorro vs mezcla aleatoria")).toHaveTextContent("25 %");
  });

  it("does not claim a saving against random when the random mix is free", async () => {
    adminApi.getRouterEvaluation.mockResolvedValue({
      ...routerReplayFixture,
      baselines: { ...routerReplayFixture.baselines, all_local: { cost: 0, quality: 0.8 } },
    });
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    fireEvent.change(slider, { target: { value: "0.75" } });
    const group = readout("Ahorro vs mezcla aleatoria");
    expect(group).toHaveTextContent("—");
    expect(group).toHaveTextContent("la mezcla aleatoria no cuesta nada a esta calidad");
  });

  it("labels the heuristic baseline as the v0 base", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });
    expect(await screen.findByText("heurística v0 (base)")).toBeInTheDocument();
  });

  it("applies the target to the selected tenant with the rest of its policy intact", async () => {
    const user = userEvent.setup();
    adminApi.getTenantPolicy.mockResolvedValue(policy);
    adminApi.updateTenantPolicy.mockResolvedValue({ ...policy, routing_quality_target: 0.9 });
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    fireEvent.change(slider, { target: { value: "0.9" } });
    await screen.findByRole("option", { name: "Default Workspace" });
    await user.click(screen.getByRole("button", { name: "Aplicar al tenant" }));

    await waitFor(() =>
      expect(adminApi.updateTenantPolicy).toHaveBeenCalledWith("nebula-admin-key", "default", {
        ...policy,
        routing_quality_target: 0.9,
      }),
    );
    expect(await screen.findByText("Objetivo 0.900 guardado en Default Workspace.")).toBeInTheDocument();
  });

  it("does not write when the tenant policy cannot be read", async () => {
    const user = userEvent.setup();
    adminApi.getTenantPolicy.mockRejectedValue(new Error("Tenant policy unavailable."));
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    await screen.findByRole("option", { name: "Default Workspace" });
    await user.click(await screen.findByRole("button", { name: "Aplicar al tenant" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Tenant policy unavailable.");
    expect(adminApi.updateTenantPolicy).not.toHaveBeenCalled();
  });

  it("says why there is no tenant to apply to when the tenant list fails", async () => {
    adminApi.listTenants.mockRejectedValue(new Error("Gateway unreachable."));
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByRole("alert")).toHaveTextContent("Gateway unreachable.");
    expect(screen.getByRole("button", { name: "Aplicar al tenant" })).toBeDisabled();
  });

  it("shows an empty state when the gateway has no replay", async () => {
    adminApi.getRouterEvaluation.mockResolvedValue(null);
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByText("No hay replay del router.")).toBeInTheDocument();
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
