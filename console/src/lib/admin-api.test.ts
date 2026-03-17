import { afterEach, describe, expect, it, vi } from "vitest";

import { createPlaygroundCompletion } from "@/lib/admin-api";

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
      provider: "openai-compatible",
      cacheHit: false,
      fallbackUsed: true,
      policyMode: "auto",
      policyOutcome: "allowed",
    });
  });
});
