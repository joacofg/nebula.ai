import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PlaygroundPage from "@/app/(console)/playground/page";
import { renderWithProviders } from "@/test/render";

const adminApi = vi.hoisted(() => ({
  listTenants: vi.fn(),
  createPlaygroundCompletion: vi.fn(),
  getUsageLedgerEntry: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    listTenants: adminApi.listTenants,
    createPlaygroundCompletion: adminApi.createPlaygroundCompletion,
    getUsageLedgerEntry: adminApi.getUsageLedgerEntry,
  };
});

describe("playground-page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.listTenants.mockResolvedValue([
      {
        id: "default",
        name: "Default Workspace",
        description: "Bootstrap tenant",
        metadata: {},
        active: true,
        created_at: "2026-03-16T12:00:00Z",
        updated_at: "2026-03-16T12:00:00Z",
      },
    ]);
    adminApi.createPlaygroundCompletion.mockResolvedValue({
      body: {
        id: "chatcmpl-play-001",
        object: "chat.completion",
        created: 1742140800,
        model: "openai/gpt-4o-mini",
        choices: [
          {
            index: 0,
            message: { role: "assistant", content: "Metadata-first response" },
            finish_reason: "stop",
          },
        ],
        usage: {
          prompt_tokens: 11,
          completion_tokens: 7,
          total_tokens: 18,
        },
        system_fingerprint: null,
      },
      errorDetail: null,
      status: 200,
      requestId: "req-123",
      tenantId: "default",
      routeTarget: "premium",
      routeReason: "direct_premium_model",
      provider: "openai-compatible",
      cacheHit: false,
      fallbackUsed: true,
      policyMode: "auto",
      policyOutcome: "allowed",
    });
    adminApi.getUsageLedgerEntry.mockResolvedValue({
      request_id: "req-123",
      tenant_id: "default",
      requested_model: "openai/gpt-4o-mini",
      final_route_target: "premium",
      final_provider: "openai-compatible",
      fallback_used: true,
      cache_hit: false,
      response_model: "openai/gpt-4o-mini",
      prompt_tokens: 19,
      completion_tokens: 8,
      total_tokens: 27,
      estimated_cost: 0.016,
      latency_ms: 180,
      timestamp: "2026-03-16T22:00:00Z",
      terminal_status: "fallback_completed",
      route_reason: "fallback",
      policy_outcome: "allowed",
    });
  });

  it("fetches the ledger entry after a successful playground mutation", async () => {
    const user = userEvent.setup();

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: "Tenant" })).toHaveValue("default");
    });
    await user.type(screen.getByLabelText("Prompt"), "Follow up in the ledger");
    await user.click(screen.getByRole("button", { name: "Run prompt" }));

    await waitFor(() => {
      expect(adminApi.getUsageLedgerEntry).toHaveBeenCalledWith("nebula-admin-key", "req-123");
    });
    expect(await screen.findByRole("heading", { name: "Immediate response evidence" })).toBeInTheDocument();
    expect(screen.getAllByText("Route reason")).toHaveLength(2);
    expect(await screen.findByText("Policy mode")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Recorded outcome" })).toBeInTheDocument();
    expect(await screen.findByText("Terminal status")).toBeInTheDocument();
    expect(await screen.findByText("fallback_completed")).toBeInTheDocument();
  });

  it("keeps the immediate response visible while the ledger lookup is pending", async () => {
    const user = userEvent.setup();
    let resolveEntry: ((value: Awaited<ReturnType<typeof adminApi.getUsageLedgerEntry>>) => void) | undefined;
    adminApi.getUsageLedgerEntry.mockReturnValue(
      new Promise((resolve) => {
        resolveEntry = resolve;
      }),
    );

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: "Tenant" })).toHaveValue("default");
    });
    await user.type(screen.getByLabelText("Prompt"), "Pending ledger data");
    await user.click(screen.getByRole("button", { name: "Run prompt" }));

    expect(await screen.findByText("Metadata-first response")).toBeInTheDocument();
    expect(screen.getByText("Loading recorded outcome...")).toBeInTheDocument();

    resolveEntry?.({
      request_id: "req-123",
      tenant_id: "default",
      requested_model: "openai/gpt-4o-mini",
      final_route_target: "premium",
      final_provider: "openai-compatible",
      fallback_used: true,
      cache_hit: false,
      response_model: "openai/gpt-4o-mini",
      prompt_tokens: 19,
      completion_tokens: 8,
      total_tokens: 27,
      estimated_cost: 0.016,
      latency_ms: 180,
      timestamp: "2026-03-16T22:00:00Z",
      terminal_status: "fallback_completed",
      route_reason: "fallback",
      policy_outcome: "allowed",
    });

    expect(
      await screen.findByText(
        "Persisted ledger evidence for the same request after Nebula records the final route, provider, fallback, and policy outcome.",
      ),
    ).toBeInTheDocument();
  });

  it("keeps metadata and recorded-outcome lookup for failed playground responses", async () => {
    const user = userEvent.setup();
    adminApi.createPlaygroundCompletion.mockResolvedValue({
      body: null,
      errorDetail: "Local provider failed.",
      status: 502,
      requestId: "req-failed-123",
      tenantId: "default",
      routeTarget: "premium",
      routeReason: "local_provider_error_fallback",
      provider: "openai-compatible",
      cacheHit: false,
      fallbackUsed: true,
      policyMode: "auto",
      policyOutcome: "allowed",
    });
    adminApi.getUsageLedgerEntry.mockResolvedValue({
      request_id: "req-failed-123",
      tenant_id: "default",
      requested_model: "nebula-auto",
      final_route_target: "premium",
      final_provider: "openai-compatible",
      fallback_used: true,
      cache_hit: false,
      response_model: null,
      prompt_tokens: 11,
      completion_tokens: 0,
      total_tokens: 11,
      estimated_cost: 0.01,
      latency_ms: 180,
      timestamp: "2026-03-16T22:00:00Z",
      terminal_status: "provider_error",
      route_reason: "local_provider_error_fallback",
      policy_outcome: "allowed",
    });

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: "Tenant" })).toHaveValue("default");
    });
    await user.type(screen.getByLabelText("Prompt"), "Recover failed response metadata");
    await user.click(screen.getByRole("button", { name: "Run prompt" }));

    expect(await screen.findByText("Local provider failed.")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Immediate response evidence" })).toBeInTheDocument();
    expect(await screen.findByText("Request ID")).toBeInTheDocument();
    expect(await screen.findByText("req-failed-123")).toBeInTheDocument();
    expect(screen.getAllByText("local_provider_error_fallback")).toHaveLength(2);
    expect(screen.getAllByText("allowed").length).toBeGreaterThanOrEqual(2);
    await waitFor(() => {
      expect(adminApi.getUsageLedgerEntry).toHaveBeenCalledWith("nebula-admin-key", "req-failed-123");
    });
    expect(await screen.findByText("provider_error")).toBeInTheDocument();
  });
});
