import { afterEach, describe, expect, it, vi } from "vitest";

import { createPlaygroundCompletion, getRouterEvaluation } from "@/lib/admin-api";

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

    await expect(getRouterEvaluation("nebula-admin-key")).rejects.toThrow("Not Found");
  });

  it("throws the gateway detail on other failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Invalid admin key." }), { status: 401 })),
    );

    await expect(getRouterEvaluation("bad")).rejects.toThrow("Invalid admin key.");
  });
});
