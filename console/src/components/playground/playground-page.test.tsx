import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PlaygroundPage from "@/app/(console)/playground/page";
import type { PlaygroundCompletionResult } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const adminApi = vi.hoisted(() => ({
  listTenants: vi.fn(),
  createPlaygroundCompletion: vi.fn(),
  getUsageLedgerEntry: vi.fn(),
  getTenantPolicy: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    listTenants: adminApi.listTenants,
    createPlaygroundCompletion: adminApi.createPlaygroundCompletion,
    getUsageLedgerEntry: adminApi.getUsageLedgerEntry,
    getTenantPolicy: adminApi.getTenantPolicy,
  };
});

const EMPTY_STATE = "Enviar un prompt para ver la respuesta y la decisión.";
const WAITING = "Esperando respuesta…";

/** A successful completion whose answer reads "A slow answer", with any field overridden. */
function completion(overrides: Partial<PlaygroundCompletionResult> = {}): PlaygroundCompletionResult {
  return {
    body: {
      id: "chatcmpl-play",
      object: "chat.completion",
      created: 1742140800,
      model: "qwen2.5",
      choices: [{ index: 0, message: { role: "assistant", content: "A slow answer" }, finish_reason: "stop" }],
      usage: { prompt_tokens: 11, completion_tokens: 7, total_tokens: 18 },
      system_fingerprint: null,
    },
    errorDetail: null,
    status: 200,
    requestId: "req-completion",
    tenantId: "default",
    routeTarget: "local",
    routeReason: "learned_router",
    routeTier: "local",
    provider: "ollama",
    cacheHit: false,
    fallbackUsed: false,
    policyMode: "auto",
    policyOutcome: "allowed",
    ...overrides,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

async function sendPrompt(user: ReturnType<typeof userEvent.setup>, prompt: string) {
  await waitFor(() => {
    expect(screen.getByRole("combobox", { name: "Tenant" })).toHaveValue("default");
  });
  await user.clear(screen.getByLabelText("Prompt"));
  await user.type(screen.getByLabelText("Prompt"), prompt);
  await user.click(screen.getByRole("button", { name: "Enviar" }));
}

describe("playground-page", () => {
  it("titles the playground and starts with an empty result", async () => {
    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByRole("heading", { level: 1, name: "Playground" })).toBeInTheDocument();
    expect(screen.getByText(EMPTY_STATE)).toBeInTheDocument();
  });

  it("names the tenant, its quality target and its routing mode in the header", async () => {
    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    const header = (await screen.findByRole("heading", { level: 1, name: "Playground" })).closest("header")!;
    expect(await within(header).findByText("Default Workspace")).toBeInTheDocument();
    expect(within(header).getByText("Objetivo")).toBeInTheDocument();
    expect(await within(header).findByText("0.90")).toBeInTheDocument();
    expect(within(header).getByText("Automático")).toBeInTheDocument();
    expect(adminApi.getTenantPolicy).toHaveBeenCalledWith("nebula-admin-key", "default");
    // What the page used to say about itself, which no operator decision depends on.
    expect(within(header).queryByText("Sin streaming")).not.toBeInTheDocument();
    expect(within(header).queryByText("Sesión")).not.toBeInTheDocument();
  });

  it("shows a dash for a target the policy does not carry, without throwing", async () => {
    adminApi.getTenantPolicy.mockResolvedValue({ routing_mode_default: "local_only" });
    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    const header = (await screen.findByRole("heading", { level: 1, name: "Playground" })).closest("header")!;
    expect(await within(header).findByText("Solo local")).toBeInTheDocument();
    expect(within(header).getByText("Objetivo")).toBeInTheDocument();
    expect(within(header).getAllByText("—")).toHaveLength(1);
    expect(within(header).getByText("Default Workspace")).toBeInTheDocument();
  });

  it("shows a dash for the target and the mode while the policy is not known", async () => {
    adminApi.getTenantPolicy.mockRejectedValue(new Error("No se pudo conectar con el gateway."));
    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    const header = (await screen.findByRole("heading", { level: 1, name: "Playground" })).closest("header")!;
    expect(await within(header).findByText("Default Workspace")).toBeInTheDocument();
    await waitFor(() => expect(adminApi.getTenantPolicy).toHaveBeenCalled());
    expect(within(header).getAllByText("—")).toHaveLength(2);
  });

  it("points to Tenants when there is no tenant to send from", async () => {
    adminApi.listTenants.mockResolvedValue([]);
    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByText("No hay tenants.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Crear tenant" })).toHaveAttribute("href", "/tenants");
    // No tenant, no policy to ask for: nothing is sent with an undefined tenant.
    const header = screen.getByRole("heading", { level: 1, name: "Playground" }).closest("header")!;
    expect(within(header).getAllByText("—")).toHaveLength(3);
    expect(adminApi.getTenantPolicy).not.toHaveBeenCalled();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.getTenantPolicy.mockResolvedValue({ routing_mode_default: "auto", routing_quality_target: 0.9 });
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
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await waitFor(() => {
      expect(adminApi.getUsageLedgerEntry).toHaveBeenCalledWith("nebula-admin-key", "req-123");
    });
    expect(await screen.findByText("Detalle de la respuesta")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Registro en el ledger" })).toBeInTheDocument();
    expect(await screen.findByText("completado con fallback")).toBeInTheDocument();
  });

  it("explains the learned router's tier from the recorded route signals", async () => {
    const user = userEvent.setup();
    adminApi.createPlaygroundCompletion.mockResolvedValue({
      body: null,
      errorDetail: null,
      status: 200,
      requestId: "req-learned",
      tenantId: "default",
      routeTarget: "premium",
      routeReason: "learned_router",
      routeTier: "economy",
      provider: "openai-compatible",
      cacheHit: false,
      fallbackUsed: false,
      policyMode: "auto",
      policyOutcome: "allowed",
    });
    adminApi.getUsageLedgerEntry.mockResolvedValue({
      request_id: "req-learned",
      tenant_id: "default",
      requested_model: "nebula-auto",
      final_route_target: "premium",
      final_provider: "openai-compatible",
      fallback_used: false,
      cache_hit: false,
      response_model: "anthropic/claude-haiku-4.5",
      prompt_tokens: 19,
      completion_tokens: 8,
      total_tokens: 27,
      estimated_cost: 0.001,
      latency_ms: 900,
      timestamp: "2026-09-30T12:00:00Z",
      terminal_status: "completed",
      route_reason: "learned_router",
      policy_outcome: "allowed",
      route_signals: {
        tier: "economy",
        p_local: 0.69,
        p_economy: 0.91,
        quality_target: 0.9,
        operating_point: { tau_local: 0.76, tau_economy: 0.9, quality: 0.903, cost_per_prompt: 0.001 },
        learned_router: "v1",
      },
    });

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });

    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: "Tenant" })).toHaveValue("default");
    });
    await user.type(screen.getByLabelText("Prompt"), "Route me");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByRole("heading", { name: "Por qué este nivel" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /economy elegido \(p 0\.91 ≥ τ 0\.90\)/ })).toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("Metadata-first response")).toBeInTheDocument();
    expect(screen.getByRole("status", { name: "Esperando el registro del ledger" })).toBeInTheDocument();

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
      await screen.findByRole("heading", { name: "Registro en el ledger" }),
    ).toBeInTheDocument();
  });

  it("keeps metadata and recorded-outcome lookup for failed playground responses", async () => {
    const user = userEvent.setup();
    adminApi.createPlaygroundCompletion.mockResolvedValue({
      body: null,
      errorDetail: "El gateway devolvió un error (502).",
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
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("El gateway devolvió un error (502).")).toBeInTheDocument();
    expect(await screen.findByText("Detalle de la respuesta")).toBeInTheDocument();
    expect(await screen.findByText("Request ID")).toBeInTheDocument();
    expect(await screen.findByText("req-failed-123")).toBeInTheDocument();
    expect(screen.getAllByText("fallback por error local")).toHaveLength(1);
    expect(screen.getByRole("group", { name: "Resultado de política" })).toHaveTextContent("Automático");
    expect(screen.queryByText("allowed")).not.toBeInTheDocument();
    await waitFor(() => {
      expect(adminApi.getUsageLedgerEntry).toHaveBeenCalledWith("nebula-admin-key", "req-failed-123");
    });
    expect(await screen.findByText("error del proveedor")).toBeInTheDocument();
  });

  it("shows the waiting state, not the empty one, while the request runs", async () => {
    const user = userEvent.setup();
    const request = deferred<PlaygroundCompletionResult>();
    adminApi.createPlaygroundCompletion.mockReturnValue(request.promise);

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });
    expect(await screen.findByText(EMPTY_STATE)).toBeInTheDocument();

    await sendPrompt(user, "A slow local model");

    expect(await screen.findByText(WAITING)).toBeInTheDocument();
    expect(screen.getByRole("status", { name: WAITING })).toBeInTheDocument();
    expect(screen.queryByText(EMPTY_STATE)).not.toBeInTheDocument();

    request.resolve(completion({ requestId: "req-slow" }));
    expect(await screen.findByText("A slow answer")).toBeInTheDocument();
    expect(screen.queryByText(WAITING)).not.toBeInTheDocument();
  });

  it("waits again, without the last answer, when a second prompt is sent", async () => {
    const user = userEvent.setup();
    adminApi.createPlaygroundCompletion.mockResolvedValueOnce(completion({ requestId: "req-first" }));
    const second = deferred<PlaygroundCompletionResult>();
    adminApi.createPlaygroundCompletion.mockReturnValueOnce(second.promise);

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });
    await sendPrompt(user, "First");
    expect(await screen.findByText("A slow answer")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText(WAITING)).toBeInTheDocument();
    expect(screen.queryByText("A slow answer")).not.toBeInTheDocument();
    expect(screen.queryByText(EMPTY_STATE)).not.toBeInTheDocument();
  });

  it("shows each fact once, with the ledger's latency written like the ledger table", async () => {
    const user = userEvent.setup();
    adminApi.createPlaygroundCompletion.mockResolvedValue(
      completion({ requestId: "req-once", routeTarget: "premium", routeTier: "economy", fallbackUsed: false }),
    );
    adminApi.getUsageLedgerEntry.mockResolvedValue({
      request_id: "req-once",
      tenant_id: "default",
      requested_model: "nebula-auto",
      final_route_target: "premium",
      final_provider: "openai-compatible",
      fallback_used: false,
      cache_hit: false,
      response_model: "anthropic/claude-haiku-4.5",
      prompt_tokens: 19,
      completion_tokens: 8,
      total_tokens: 27,
      estimated_cost: 0.001,
      latency_ms: 21345,
      timestamp: "2026-09-30T12:00:00Z",
      terminal_status: "completed",
      route_reason: "learned_router",
      policy_outcome: "allowed",
      route_signals: {
        tier: "economy",
        p_local: 0.69,
        p_economy: 0.91,
        quality_target: 0.9,
        operating_point: { tau_local: 0.76, tau_economy: 0.9, quality: 0.903, cost_per_prompt: 0.001 },
        learned_router: "v1",
      },
    });

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });
    await sendPrompt(user, "One fact, one place");
    expect(await screen.findByRole("heading", { name: "Registro en el ledger" })).toBeInTheDocument();

    for (const fact of ["Ruta", "Motivo", "Nivel", "Proveedor", "Caché", "Fallback", "Latencia"]) {
      expect(screen.getAllByRole("group", { name: fact }), fact).toHaveLength(1);
    }
    // The single latency is the ledger's, in the ledger table's format (seconds from 1000 ms).
    expect(screen.getByRole("group", { name: "Latencia" })).toHaveTextContent("21.3 s");
    expect(screen.queryByText(/21345/)).not.toBeInTheDocument();
    // What only the live response carries stays in the folded detail.
    expect(screen.getByRole("group", { name: "Request ID" })).toHaveTextContent("req-once");
    // With the ledger record, the facts are the ledger block's and the detail does not repeat them.
    const detail = within(screen.getByText("Detalle de la respuesta").closest("details")!);
    const ledger = within(screen.getByRole("region", { name: "Registro en el ledger" }));
    for (const fact of ["Ruta", "Motivo", "Nivel", "Proveedor", "Caché", "Fallback"]) {
      expect(ledger.getByRole("group", { name: fact }), fact).toBeInTheDocument();
      expect(detail.queryByRole("group", { name: fact }), fact).not.toBeInTheDocument();
    }
    // The policy rows are labels, never the gateway's codes.
    expect(detail.getByRole("group", { name: "Modo de política" })).toHaveTextContent("Automático");
    expect(detail.getByRole("group", { name: "Resultado de política" })).toHaveTextContent("Automático");
  });

  it.each([
    ["the ledger lookup fails", () => adminApi.getUsageLedgerEntry.mockRejectedValue(new Error("No se pudo leer el ledger."))],
    ["the ledger has no record of the request", () => adminApi.getUsageLedgerEntry.mockResolvedValue(null)],
  ])("falls back to the facts of the response headers, each once, when %s", async (_name, arrange) => {
    const user = userEvent.setup();
    arrange();
    adminApi.createPlaygroundCompletion.mockResolvedValue(
      completion({
        requestId: "req-headers",
        routeTarget: "premium",
        routeReason: "learned_router",
        routeTier: "economy",
        provider: "openai-compatible",
        fallbackUsed: true,
        policyMode: "premium_only",
        policyOutcome: "routing_mode=premium_only;denied=Request exceeds the tenant premium spend guardrail.",
      }),
    );

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });
    await sendPrompt(user, "No ledger record");
    expect(await screen.findByText("A slow answer")).toBeInTheDocument();
    await waitFor(() => expect(adminApi.getUsageLedgerEntry).toHaveBeenCalledWith("nebula-admin-key", "req-headers"));
    await waitFor(() => expect(screen.queryByRole("status", { name: "Esperando el registro del ledger" })).not.toBeInTheDocument());

    expect(screen.queryByRole("heading", { name: "Registro en el ledger" })).not.toBeInTheDocument();
    for (const fact of ["Ruta", "Motivo", "Nivel", "Proveedor", "Caché", "Fallback"]) {
      expect(screen.getAllByRole("group", { name: fact }), fact).toHaveLength(1);
    }
    expect(screen.getByRole("group", { name: "Ruta" })).toHaveTextContent("Premium");
    expect(screen.getByRole("group", { name: "Motivo" })).toHaveTextContent("router aprendido");
    expect(screen.getByRole("group", { name: "Nivel" })).toHaveTextContent("economy");
    expect(screen.getByRole("group", { name: "Fallback" })).toHaveTextContent("sí");
    expect(screen.getByRole("group", { name: "Resultado de política" })).toHaveTextContent("Solo premium, denegado");
    expect(screen.queryByText(/routing_mode|denied=|premium_only/)).not.toBeInTheDocument();
  });

  it("reads Caché and Fallback as a dash, not as no, when the response headers did not send them", async () => {
    const user = userEvent.setup();
    adminApi.getUsageLedgerEntry.mockResolvedValue(null);
    adminApi.createPlaygroundCompletion.mockResolvedValue(
      completion({ requestId: "req-bare", cacheHit: null, fallbackUsed: null }),
    );

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });
    await sendPrompt(user, "Bare headers");
    expect(await screen.findByText("A slow answer")).toBeInTheDocument();
    await waitFor(() => expect(adminApi.getUsageLedgerEntry).toHaveBeenCalledWith("nebula-admin-key", "req-bare"));

    await waitFor(() => expect(screen.getByRole("group", { name: "Caché" })).toHaveTextContent("—"));
    expect(screen.getByRole("group", { name: "Fallback" })).toHaveTextContent("—");
  });

  it("waits for the ledger record before showing the routing facts, then shows them once in its block", async () => {
    const user = userEvent.setup();
    const lookup = deferred<Awaited<ReturnType<typeof adminApi.getUsageLedgerEntry>>>();
    adminApi.getUsageLedgerEntry.mockReturnValue(lookup.promise);
    adminApi.createPlaygroundCompletion.mockResolvedValue(completion({ requestId: "req-late" }));

    renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });
    await sendPrompt(user, "Slow ledger");
    expect(await screen.findByRole("status", { name: "Esperando el registro del ledger" })).toBeInTheDocument();
    // Not the headers' copy now, which the ledger block would repeat in a moment.
    for (const fact of ["Ruta", "Nivel", "Caché"]) {
      expect(screen.queryByRole("group", { name: fact }), fact).not.toBeInTheDocument();
    }

    lookup.resolve({
      request_id: "req-late",
      tenant_id: "default",
      requested_model: "nebula-auto",
      final_route_target: "local",
      final_provider: "ollama",
      fallback_used: false,
      cache_hit: false,
      response_model: "qwen2.5",
      prompt_tokens: 5,
      completion_tokens: 5,
      total_tokens: 10,
      estimated_cost: 0,
      latency_ms: 900,
      timestamp: "2026-09-30T12:00:00Z",
      terminal_status: "completed",
      route_reason: "learned_router",
      policy_outcome: "default",
    });
    expect(await screen.findByRole("region", { name: "Registro en el ledger" })).toBeInTheDocument();
    for (const fact of ["Ruta", "Motivo", "Nivel", "Proveedor", "Caché", "Fallback", "Latencia"]) {
      expect(screen.getAllByRole("group", { name: fact }), fact).toHaveLength(1);
    }
  });

  it("shows a request that could not be sent and leaves no rejection unhandled", async () => {
    const user = userEvent.setup();
    const unhandled = vi.fn();
    process.on("unhandledRejection", unhandled);
    try {
      adminApi.createPlaygroundCompletion.mockRejectedValue(new Error("No se pudo conectar con el gateway."));

      renderWithProviders(<PlaygroundPage />, { adminKey: "nebula-admin-key" });
      await sendPrompt(user, "The gateway is down");

      expect(await screen.findByText("No se pudo conectar con el gateway.")).toBeInTheDocument();
      expect(screen.queryByText(WAITING)).not.toBeInTheDocument();
      // Node reports an unhandled rejection once the microtask queue drains: wait one macrotask.
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(unhandled).not.toHaveBeenCalled();
    } finally {
      process.off("unhandledRejection", unhandled);
    }
  });
});
