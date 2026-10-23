import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import EvaluationPage from "@/app/(console)/evaluacion/page";
import PlaygroundPage from "@/app/(console)/playground/page";
import PolicyPage from "@/app/(console)/policy/page";
import TenantsPage from "@/app/(console)/tenants/page";
import * as adminApi from "@/lib/admin-api";
import type { TenantPolicy, TenantRecord } from "@/lib/admin-api";
import { SelectedTenantProvider, useSelectedTenant } from "@/lib/selected-tenant";
import { renderWithProviders } from "@/test/render";
import { routerReplayFixture } from "@/test/router-replay-fixture";

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    getRouterEvaluation: vi.fn(),
    listTenants: vi.fn(),
    getTenantPolicy: vi.fn(),
    getPolicyOptions: vi.fn(),
    updateTenantPolicy: vi.fn(),
    simulateTenantPolicy: vi.fn(),
  };
});

function record(id: string, name: string): TenantRecord {
  return {
    id,
    name,
    description: null,
    metadata: {},
    active: true,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:00:00Z",
  };
}

const ALPHA = record("tenant-alpha", "Alpha");
const BRAVO = record("tenant-bravo", "Bravo");

/** Stands in for a page: shows what the hook returns and lets the test pick another tenant. */
function Page({ name, tenants }: { name: string; tenants: TenantRecord[] | undefined }) {
  const { tenantId, tenant, setTenantId } = useSelectedTenant(tenants);
  return (
    <section aria-label={name}>
      <output aria-label={`${name} id`}>{String(tenantId)}</output>
      <output aria-label={`${name} name`}>{tenant ? tenant.name : "none"}</output>
      <button type="button" onClick={() => setTenantId(BRAVO.id)}>
        {`${name}: elegir Bravo`}
      </button>
    </section>
  );
}

describe("useSelectedTenant", () => {
  it("selects the first tenant when none was chosen", () => {
    render(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[ALPHA, BRAVO]} />
      </SelectedTenantProvider>,
    );
    expect(screen.getByLabelText("policy id")).toHaveTextContent("tenant-alpha");
    expect(screen.getByLabelText("policy name")).toHaveTextContent("Alpha");
  });

  it("keeps the tenant chosen on one page when another page mounts", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[ALPHA, BRAVO]} />
      </SelectedTenantProvider>,
    );
    await user.click(screen.getByRole("button", { name: "policy: elegir Bravo" }));

    rerender(
      <SelectedTenantProvider>
        <Page name="playground" tenants={[ALPHA, BRAVO]} />
      </SelectedTenantProvider>,
    );

    expect(screen.getByLabelText("playground id")).toHaveTextContent("tenant-bravo");
    expect(screen.getByLabelText("playground name")).toHaveTextContent("Bravo");
  });

  it("returns nulls while the list is loading or empty, and keeps the choice for later", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[ALPHA, BRAVO]} />
      </SelectedTenantProvider>,
    );
    await user.click(screen.getByRole("button", { name: "policy: elegir Bravo" }));

    rerender(
      <SelectedTenantProvider>
        <Page name="policy" tenants={undefined} />
      </SelectedTenantProvider>,
    );
    expect(screen.getByLabelText("policy id")).toHaveTextContent("null");
    expect(screen.getByLabelText("policy name")).toHaveTextContent("none");

    rerender(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[]} />
      </SelectedTenantProvider>,
    );
    expect(screen.getByLabelText("policy id")).toHaveTextContent("null");

    rerender(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[ALPHA, BRAVO]} />
      </SelectedTenantProvider>,
    );
    expect(screen.getByLabelText("policy id")).toHaveTextContent("tenant-bravo");
  });

  it("falls back to the first tenant when the chosen id is no longer in the list, and stores it", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[ALPHA, BRAVO]} />
      </SelectedTenantProvider>,
    );
    await user.click(screen.getByRole("button", { name: "policy: elegir Bravo" }));

    rerender(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[ALPHA]} />
      </SelectedTenantProvider>,
    );
    expect(screen.getByLabelText("policy id")).toHaveTextContent("tenant-alpha");

    // The fallback was stored: a list that has Bravo again does not bring the old choice back.
    rerender(
      <SelectedTenantProvider>
        <Page name="policy" tenants={[ALPHA, BRAVO]} />
      </SelectedTenantProvider>,
    );
    expect(screen.getByLabelText("policy id")).toHaveTextContent("tenant-alpha");
  });

  it("fails loudly outside the provider", () => {
    const error = console.error;
    console.error = () => undefined;
    try {
      expect(() => render(<Page name="policy" tenants={[ALPHA]} />)).toThrow(
        "useSelectedTenant must be used inside SelectedTenantProvider.",
      );
    } finally {
      console.error = error;
    }
  });
});

const POLICY: TenantPolicy = {
  routing_mode_default: "auto",
  calibrated_routing_enabled: true,
  allowed_premium_models: ["openai/gpt-4o-mini"],
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

function tenantSelect() {
  return screen.getByRole("combobox", { name: "Tenant" });
}

async function expectTenantSelect(value: string) {
  await waitFor(() => expect(tenantSelect()).toHaveValue(value));
}

describe("pages that work on one tenant", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Keeps the Evaluación replay paused, as in its own page tests.
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("reduce"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })) as unknown as typeof window.matchMedia;
    vi.mocked(adminApi.getRouterEvaluation).mockResolvedValue(routerReplayFixture);
    vi.mocked(adminApi.listTenants).mockResolvedValue([ALPHA, BRAVO]);
    vi.mocked(adminApi.getTenantPolicy).mockResolvedValue(POLICY);
    vi.mocked(adminApi.getPolicyOptions).mockResolvedValue({
      routing_modes: ["auto", "local_only", "premium_only"],
      known_premium_models: ["openai/gpt-4o-mini"],
      default_premium_model: "openai/gpt-4o-mini",
      runtime_enforced_fields: [],
      soft_signal_fields: [],
      advisory_fields: [],
    });
  });

  it("keeps the tenant picked on Política when moving to Playground and to Evaluación", async () => {
    const user = userEvent.setup();
    const view = renderWithProviders(<PolicyPage />, { adminKey: "admin-key" });

    await expectTenantSelect("tenant-alpha");
    await user.selectOptions(tenantSelect(), "tenant-bravo");

    view.rerender(<PlaygroundPage />);
    await expectTenantSelect("tenant-bravo");

    view.rerender(<EvaluationPage />);
    await expectTenantSelect("tenant-bravo");
  });

  it("updates the other pages when the tenant is picked on Playground", async () => {
    const user = userEvent.setup();
    const view = renderWithProviders(<PlaygroundPage />, { adminKey: "admin-key" });

    await expectTenantSelect("tenant-alpha");
    await user.selectOptions(tenantSelect(), "tenant-bravo");

    view.rerender(<PolicyPage />);
    await expectTenantSelect("tenant-bravo");
    await waitFor(() => expect(adminApi.getTenantPolicy).toHaveBeenLastCalledWith("admin-key", "tenant-bravo"));
  });

  it("follows the tenant opened on Tenants into Política", async () => {
    const user = userEvent.setup();
    const view = renderWithProviders(<TenantsPage />, { adminKey: "admin-key" });

    await user.click(await screen.findByRole("row", { name: /Bravo/ }));
    expect(screen.getByRole("heading", { name: "Editar Bravo" })).toBeInTheDocument();

    view.rerender(<PolicyPage />);
    await expectTenantSelect("tenant-bravo");
  });

  it("shows the empty state and sends no tenant-scoped request when there are no tenants", async () => {
    vi.mocked(adminApi.listTenants).mockResolvedValue([]);
    const view = renderWithProviders(<PolicyPage />, { adminKey: "admin-key" });
    expect(await screen.findByText("No hay tenants.")).toBeInTheDocument();

    view.rerender(<PlaygroundPage />);
    expect(await screen.findByText("No hay tenants.")).toBeInTheDocument();

    expect(adminApi.getTenantPolicy).not.toHaveBeenCalled();
    expect(adminApi.simulateTenantPolicy).not.toHaveBeenCalled();
  });

  it("falls back to the first tenant when the one picked elsewhere is gone", async () => {
    const user = userEvent.setup();
    const view = renderWithProviders(<PolicyPage />, { adminKey: "admin-key" });
    await expectTenantSelect("tenant-alpha");
    await user.selectOptions(tenantSelect(), "tenant-bravo");

    vi.mocked(adminApi.listTenants).mockResolvedValue([ALPHA]);
    view.rerender(<EvaluationPage />);
    await expectTenantSelect("tenant-alpha");
    expect(screen.getByRole("button", { name: "Aplicar al tenant" })).toBeEnabled();
  });
});
