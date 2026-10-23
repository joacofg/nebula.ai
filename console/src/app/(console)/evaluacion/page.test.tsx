import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import EvaluationPage from "@/app/(console)/evaluacion/page";
import { AdminApiError, type TenantPolicy } from "@/lib/admin-api";
import { useSelectedTenant } from "@/lib/selected-tenant";
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

const acme = { ...tenants[0], id: "acme", name: "Acme Robotics" };

/** The shared tenant selection, as the next page (Playground) reads it. */
function SelectedTenantProbe() {
  const { tenantId } = useSelectedTenant([...tenants, acme]);
  return <output aria-label="Tenant seleccionado">{tenantId}</output>;
}

/** A reading of the slider panel; the replay feed below repeats some labels, so look outside it. */
function readout(name: string) {
  const replay = screen.getByRole("region", { name: /^Replay acelerado/ });
  const [panel] = screen.getAllByRole("group", { name }).filter((group) => !replay.contains(group));
  return panel;
}

describe("evaluation page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.getTenantPolicy.mockResolvedValue(policy);
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

  it("leads the readouts with the saving against all-frontier, the only emphasized one", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    await screen.findByRole("slider", { name: "Calidad objetivo" });
    const saving = readout("Ahorro vs todo frontier");
    // 0.95 picks the (0.7, 0.9) point: USD 2.50 against USD 4.00 for all-frontier.
    const value = within(saving).getByText("38 %");
    expect(value).toHaveAttribute("data-emphasis", "true");
    const [first] = within(saving.closest("dl") as HTMLElement).getAllByRole("group");
    expect(first).toBe(saving);
    expect(within(readout("Costo por 1000 pedidos")).getByText("USD 2.50")).not.toHaveAttribute("data-emphasis");
    expect(within(readout("Calidad medida")).getByText("1.000")).not.toHaveAttribute("data-emphasis");
  });

  it("gives each language's quality and cost per 1000 requests their units", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    await screen.findByRole("slider", { name: "Calidad objetivo" });
    // Spanish: one local, one economy prompt, both accepted; English: both to frontier.
    expect(readout("Español · 2 pedidos")).toHaveTextContent("calidad 1.000 · USD 1.00 / 1000");
    expect(readout("Inglés · 2 pedidos")).toHaveTextContent("calidad 1.000 · USD 4.00 / 1000");
  });

  it("names the model behind each tier in the tier share", async () => {
    adminApi.getRouterEvaluation.mockResolvedValue({
      ...routerReplayFixture,
      latency: {
        ...routerReplayFixture.latency,
        haiku: { model: "anthropic/claude-haiku-4.5", median_s: 3.9, p90_s: 6.4, mean_s: 4.2, n: 30 },
        llama3b: { model: "llama3.2:3b", median_s: 9.8, p90_s: 17.4, mean_s: 9.5, n: 30 },
      },
    });
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const share = await screen.findByRole("list", { name: "Reparto por nivel" });
    const [local, economy, frontier] = within(share).getAllByRole("listitem");
    expect(local).toHaveTextContent(/local\s*qwen2\.5:7b/);
    expect(economy).toHaveTextContent(/economy\s*anthropic\/claude-haiku-4\.5/);
    expect(frontier).toHaveTextContent(/frontier\s*openai\/gpt-4\.1/);
    expect(share).not.toHaveTextContent("llama3.2:3b");
  });

  it("shows only the tier name when the replay did not measure its model", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const share = await screen.findByRole("list", { name: "Reparto por nivel" });
    const [, economy] = within(share).getAllByRole("listitem");
    expect(economy).toHaveTextContent(/^economy\s*\d+ %$/);
  });

  it("calls the judges the judge ensemble in the replay caption", async () => {
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const replay = await screen.findByRole("region", { name: /^Replay acelerado/ });
    expect(replay).toHaveTextContent("si el ensamble de jueces aceptó la respuesta de ese nivel");
    expect(replay).not.toHaveTextContent("los jueces");
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
    expect(await screen.findByText("Objetivo 0.90 guardado en Default Workspace.")).toBeInTheDocument();
  });

  it("opens the slider at the selected tenant's target and says what that target is", async () => {
    adminApi.getTenantPolicy.mockResolvedValue({ ...policy, routing_quality_target: 0.9 });
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByText("Objetivo actual 0.90")).toBeInTheDocument();
    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    await waitFor(() => expect(slider).toHaveValue("0.9"));
    expect(adminApi.getTenantPolicy).toHaveBeenCalledWith("nebula-admin-key", "default");
  });

  it("opens at 0.95 while the tenant's target is not known, and does not ask for a policy without a tenant", async () => {
    adminApi.listTenants.mockResolvedValue([]);
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    expect(slider).toHaveValue("0.95");
    await screen.findByRole("option", { name: "Sin tenants" });
    expect(screen.queryByText(/Objetivo actual/)).not.toBeInTheDocument();
    expect(adminApi.getTenantPolicy).not.toHaveBeenCalled();
  });

  it("keeps the slider usable when the tenant's policy cannot be read", async () => {
    adminApi.getTenantPolicy.mockRejectedValue(new Error("Tenant policy unavailable."));
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    expect(await screen.findByText("Objetivo actual —")).toBeInTheDocument();
    expect(slider).toHaveValue("0.95");
    fireEvent.change(slider, { target: { value: "0.8" } });
    expect(slider).toHaveValue("0.8");
  });

  it("follows the tenant: switching tenants opens the slider at that tenant's target", async () => {
    const user = userEvent.setup();
    adminApi.listTenants.mockResolvedValue([...tenants, acme]);
    adminApi.getTenantPolicy.mockImplementation(async (_key: string, id: string) =>
      id === "acme" ? { ...policy, routing_quality_target: 0.9 } : policy,
    );
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    expect(await screen.findByText("Objetivo actual 0.95")).toBeInTheDocument();
    fireEvent.change(slider, { target: { value: "0.8" } });

    await screen.findByRole("option", { name: "Acme Robotics" });
    await user.selectOptions(screen.getByRole("combobox", { name: "Tenant" }), "acme");

    expect(await screen.findByText("Objetivo actual 0.90")).toBeInTheDocument();
    await waitFor(() => expect(slider).toHaveValue("0.9"));
  });

  it("offers Playground for the same tenant through the shared selection", async () => {
    const user = userEvent.setup();
    adminApi.listTenants.mockResolvedValue([...tenants, acme]);
    renderWithProviders(
      <>
        <EvaluationPage />
        <SelectedTenantProbe />
      </>,
      { adminKey: "nebula-admin-key" },
    );

    await screen.findByRole("option", { name: "Acme Robotics" });
    await user.selectOptions(screen.getByRole("combobox", { name: "Tenant" }), "acme");

    expect(screen.getByRole("link", { name: "Probar en Playground" })).toHaveAttribute("href", "/playground");
    expect(screen.getByLabelText("Tenant seleccionado")).toHaveTextContent("acme");
  });

  it("clears the saved message as soon as the slider moves", async () => {
    const user = userEvent.setup();
    adminApi.updateTenantPolicy.mockResolvedValue({ ...policy, routing_quality_target: 0.9 });
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    const slider = await screen.findByRole("slider", { name: "Calidad objetivo" });
    fireEvent.change(slider, { target: { value: "0.9" } });
    await screen.findByRole("option", { name: "Default Workspace" });
    await user.click(screen.getByRole("button", { name: "Aplicar al tenant" }));
    expect(await screen.findByText("Objetivo 0.90 guardado en Default Workspace.")).toBeInTheDocument();
    expect(screen.getByText("Objetivo actual 0.90")).toBeInTheDocument();

    fireEvent.change(slider, { target: { value: "0.85" } });

    await waitFor(() => expect(screen.queryByText(/guardado en/)).not.toBeInTheDocument());
  });

  it("says why applying the target failed, in Spanish by status", async () => {
    const user = userEvent.setup();
    adminApi.getTenantPolicy.mockResolvedValue(policy);
    adminApi.updateTenantPolicy.mockRejectedValue(new AdminApiError(403, "Tenant policy denied."));
    renderWithProviders(<EvaluationPage />, { adminKey: "nebula-admin-key" });

    await screen.findByRole("option", { name: "Default Workspace" });
    await user.click(await screen.findByRole("button", { name: "Aplicar al tenant" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo aplicar: Acción no permitida.");
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
