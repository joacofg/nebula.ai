import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AdminApiError,
  createPlaygroundCompletion,
  getRouterEvaluation,
  listTenants,
  listUsageLedger,
} from "@/lib/admin-api";

function jsonResponse(body: unknown, status: number, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

describe("admin-api playground completion", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("preserves request metadata from failed playground responses so recorded-outcome lookup can continue", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Local provider failed." }), {
          status: 502,
          headers: {
            "Content-Type": "application/json",
            "X-Request-ID": "req-failed-123",
            "X-Nebula-Tenant-ID": "default",
            "X-Nebula-Route-Target": "premium",
            "X-Nebula-Route-Reason": "local_provider_error_fallback",
            "X-Nebula-Route-Tier": "frontier",
            "X-Nebula-Provider": "openai-compatible",
            "X-Nebula-Cache-Hit": "false",
            "X-Nebula-Fallback-Used": "true",
            "X-Nebula-Policy-Mode": "auto",
            "X-Nebula-Policy-Outcome": "allowed",
          },
        }),
      ),
    );

    await expect(
      createPlaygroundCompletion("nebula-admin-key", {
        tenantId: "default",
        model: "nebula-auto",
        prompt: "Recover failed response metadata",
      }),
    ).resolves.toMatchObject({
      requestId: "req-failed-123",
      tenantId: "default",
      routeTarget: "premium",
      routeReason: "local_provider_error_fallback",
      routeTier: "frontier",
      provider: "openai-compatible",
      cacheHit: false,
      fallbackUsed: true,
      policyMode: "auto",
      policyOutcome: "allowed",
    });
  });
});

describe("admin-api router evaluation", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the replay payload from the admin proxy", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ version: 1, router_label: "v1", rows: [] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getRouterEvaluation("nebula-admin-key")).resolves.toMatchObject({ version: 1 });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/evaluation/router",
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Nebula-Admin-Key": "nebula-admin-key" }),
      }),
    );
  });

  it("returns null when the gateway has no replay file", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "No router replay" }), { status: 404 })),
    );

    await expect(getRouterEvaluation("nebula-admin-key")).resolves.toBeNull();
  });

  it("treats a 404 that is not the missing replay as an error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Not Found" }), { status: 404 })),
    );

    await expect(getRouterEvaluation("nebula-admin-key")).rejects.toThrow("No se encontró el recurso.");
  });

  it("throws the Spanish message of the status on other failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Invalid admin key." }), { status: 401 })),
    );

    await expect(getRouterEvaluation("bad")).rejects.toThrow("La clave de admin no es válida.");
  });
});

describe("admin-api usage ledger query", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  async function requestedUrl(filters: Parameters<typeof listUsageLedger>[1]) {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([], 200));
    vi.stubGlobal("fetch", fetchMock);
    await listUsageLedger("nebula-admin-key", filters);
    return new URL(String(fetchMock.mock.calls[0][0]), "http://console.test");
  }

  it("sends the tier filter next to the other filters", async () => {
    const url = await requestedUrl({
      tenantId: "acme",
      routeTarget: "premium",
      tier: "economy",
      terminalStatus: "client_disconnected",
      fromTimestamp: "2026-10-22T13:00:00.000Z",
      toTimestamp: "2026-10-22T16:00:00.000Z",
    });

    expect(url.pathname).toBe("/api/admin/usage/ledger");
    expect(Object.fromEntries(url.searchParams)).toEqual({
      tenant_id: "acme",
      route_target: "premium",
      tier: "economy",
      terminal_status: "client_disconnected",
      from_timestamp: "2026-10-22T13:00:00.000Z",
      to_timestamp: "2026-10-22T16:00:00.000Z",
    });
  });

  it("sends no parameter for a filter left empty", async () => {
    const url = await requestedUrl({ tenantId: "", routeTarget: "", tier: "", terminalStatus: "" });

    expect(url.search).toBe("");
  });
});

describe("admin-api error messages", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  async function failure(response: Response | Error) {
    vi.stubGlobal(
      "fetch",
      response instanceof Error ? vi.fn().mockRejectedValue(response) : vi.fn().mockResolvedValue(response),
    );
    const error = await listTenants("nebula-admin-key").then(
      () => null,
      (reason: unknown) => reason,
    );
    expect(error).toBeInstanceOf(AdminApiError);
    return error as AdminApiError;
  }

  it.each([
    [401, "Missing or invalid admin API key.", "La clave de admin no es válida."],
    [403, "Tenant policy denied the request.", "Acción no permitida."],
    [404, "Tenant not found.", "No se encontró el recurso."],
    [409, "Tenant already exists.", "Ya existe un recurso con ese identificador."],
    [400, "Bad payload.", "El gateway rechazó los datos."],
    [422, "Unprocessable.", "El gateway rechazó los datos."],
    [500, "Internal Server Error", "El gateway devolvió un error (500)."],
    [502, "Bad gateway.", "El gateway devolvió un error (502)."],
  ])("maps HTTP %i to its Spanish message and keeps the English detail", async (status, detail, message) => {
    const error = await failure(jsonResponse({ detail }, status));

    expect(error.message).toBe(message);
    expect(error.status).toBe(status);
    expect(error.detail).toBe(detail);
  });

  it("names the invalid fields of a FastAPI 422 list by the last location element", async () => {
    const error = await failure(
      jsonResponse(
        {
          detail: [
            { loc: ["body", "name"], msg: "Field required", type: "missing" },
            { loc: ["body", "tenant_id"], msg: "Field required", type: "missing" },
          ],
        },
        422,
      ),
    );

    expect(error.message).toBe("Revisar los campos: name, tenant_id.");
  });

  it("does not repeat a field or print a list index as a field", async () => {
    const error = await failure(
      jsonResponse(
        {
          detail: [
            { loc: ["body", "messages", 0, "content"], msg: "bad", type: "x" },
            { loc: ["body", "messages", 1, "content"], msg: "bad", type: "x" },
            { loc: ["body", "messages", 2], msg: "bad", type: "x" },
          ],
        },
        422,
      ),
    );

    expect(error.message).toBe("Revisar los campos: content, messages.");
  });

  it("falls back to the rejected-data message for a 422 list without usable fields", async () => {
    const error = await failure(jsonResponse({ detail: [{ loc: [], msg: "bad", type: "x" }] }, 422));

    expect(error.message).toBe("El gateway rechazó los datos.");
  });

  it("tells the caller how long to wait on a 429 with Retry-After", async () => {
    const error = await failure(jsonResponse({ detail: "Rate limit exceeded." }, 429, { "Retry-After": "7" }));

    expect(error.message).toBe("Demasiados pedidos. Reintentar en 7 s.");
    expect(error.retryAfterSeconds).toBe(7);
  });

  it("asks for a short wait on a 429 without a usable Retry-After", async () => {
    const withoutHeader = await failure(jsonResponse({ detail: "Rate limit exceeded." }, 429));
    const withDate = await failure(
      jsonResponse({ detail: "Rate limit exceeded." }, 429, { "Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT" }),
    );

    expect(withoutHeader.message).toBe("Demasiados pedidos. Reintentar en unos segundos.");
    expect(withoutHeader.retryAfterSeconds).toBeNull();
    expect(withDate.message).toBe("Demasiados pedidos. Reintentar en unos segundos.");
    expect(withDate.retryAfterSeconds).toBeNull();
  });

  it("shows the gateway-unreachable message when the proxy answers 503 gateway_unreachable", async () => {
    const error = await failure(jsonResponse({ detail: "gateway_unreachable" }, 503));

    expect(error.message).toBe("No se pudo conectar con el gateway.");
    expect(error.status).toBe(503);
  });

  it("shows the gateway-unreachable message when the request itself cannot be sent", async () => {
    const error = await failure(new TypeError("Failed to fetch"));

    expect(error.message).toBe("No se pudo conectar con el gateway.");
  });

  it("maps a failure whose body is not JSON by its status alone", async () => {
    const error = await failure(new Response("<html>Internal Server Error</html>", { status: 500 }));

    expect(error.message).toBe("El gateway devolvió un error (500).");
    expect(error.detail).toBeNull();
  });

  it("applies the same mapping to the router replay request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "Not Found" }, 404)));

    await expect(getRouterEvaluation("nebula-admin-key")).rejects.toMatchObject({
      name: "AdminApiError",
      message: "No se encontró el recurso.",
    });
  });
});

describe("admin-api playground errors", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const input = { tenantId: "default", model: "nebula-auto", prompt: "hola" };

  it("reports a failed completion with the Spanish message by status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "Local provider failed." }, 502)));

    await expect(createPlaygroundCompletion("nebula-admin-key", input)).resolves.toMatchObject({
      body: null,
      status: 502,
      errorDetail: "El gateway devolvió un error (502).",
    });
  });

  it("reports an unreachable gateway answered by the proxy", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "gateway_unreachable" }, 503)));

    await expect(createPlaygroundCompletion("nebula-admin-key", input)).resolves.toMatchObject({
      body: null,
      errorDetail: "No se pudo conectar con el gateway.",
    });
  });

  it("throws the unreachable error when the request cannot be sent", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(createPlaygroundCompletion("nebula-admin-key", input)).rejects.toMatchObject({
      name: "AdminApiError",
      message: "No se pudo conectar con el gateway.",
    });
  });
});
