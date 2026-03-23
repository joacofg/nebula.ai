import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createPlaygroundCompletion,
  listRemoteActions,
  queueRotateDeploymentCredential,
} from "@/lib/admin-api";

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

describe("admin-api remote actions", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts the operator note when queueing a hosted credential rotation", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "action-1",
          deployment_id: "dep-1",
          action_type: "rotate_deployment_credential",
          status: "queued",
          note: "Rotate after review",
          requested_at: "2026-03-22T12:00:00Z",
          expires_at: "2026-03-22T12:15:00Z",
          started_at: null,
          finished_at: null,
          failure_reason: null,
          failure_detail: null,
          result_credential_prefix: null,
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      queueRotateDeploymentCredential("nebula-admin-key", "dep-1", "Rotate after review"),
    ).resolves.toMatchObject({
      id: "action-1",
      note: "Rotate after review",
      status: "queued",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/deployments/dep-1/remote-actions/rotate-credential",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          "X-Nebula-Admin-Key": "nebula-admin-key",
        }),
        body: JSON.stringify({ note: "Rotate after review" }),
      }),
    );
  });

  it("loads recent remote action history for a deployment", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: "action-2",
            deployment_id: "dep-1",
            action_type: "rotate_deployment_credential",
            status: "applied",
            note: "Rotated cleanly",
            requested_at: "2026-03-22T12:00:00Z",
            expires_at: "2026-03-22T12:15:00Z",
            started_at: "2026-03-22T12:01:00Z",
            finished_at: "2026-03-22T12:02:00Z",
            failure_reason: null,
            failure_detail: null,
            result_credential_prefix: "nbdc_abcd1234",
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(listRemoteActions("nebula-admin-key", "dep-1")).resolves.toMatchObject([
      {
        id: "action-2",
        status: "applied",
        result_credential_prefix: "nbdc_abcd1234",
      },
    ]);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/deployments/dep-1/remote-actions",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          "X-Nebula-Admin-Key": "nebula-admin-key",
        }),
      }),
    );
  });
});
