import { inspect } from "node:util";

import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET, POST } from "./route";

const context = (...path: string[]) => ({ params: Promise.resolve({ path }) });
// What a log line must never carry: the operator's admin key, and anything from the request body.
const ADMIN_KEY = "nb-admin-secret-7f3a";
const BODY_MARKER = "body-marker-4c1e";

describe("admin proxy", () => {
  const consoleError = vi.spyOn(console, "error");

  beforeEach(() => {
    consoleError.mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    consoleError.mockReset();
  });

  it("forwards the gateway answer with its status and headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "slow down" }), {
        status: 429,
        headers: { "Content-Type": "application/json", "Retry-After": "7" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(new NextRequest("http://console.test/api/admin/tenants?x=1"), context("tenants"));

    expect(response.status).toBe(429);
    expect(response.headers.get("Retry-After")).toBe("7");
    await expect(response.json()).resolves.toEqual({ detail: "slow down" });
    expect(String(fetchMock.mock.calls[0][0])).toContain("/v1/admin/tenants?x=1");
  });

  it("forwards the method, body and admin key, and drops hop-by-hop request headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const body = JSON.stringify({ name: "Tenant A" });

    await POST(
      new NextRequest("http://console.test/api/admin/tenants", {
        method: "POST",
        headers: {
          "X-Nebula-Admin-Key": ADMIN_KEY,
          "Content-Type": "application/json",
          Connection: "keep-alive",
          "Keep-Alive": "timeout=5",
        },
        body,
      }),
      context("tenants"),
    );

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Headers;
    expect(init.method).toBe("POST");
    expect(init.body).toBe(body);
    expect(headers.get("X-Nebula-Admin-Key")).toBe(ADMIN_KEY);
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.has("connection")).toBe(false);
    expect(headers.has("keep-alive")).toBe(false);
  });

  it("sends a GET without a body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await GET(
      new NextRequest("http://console.test/api/admin/tenants", { headers: { "X-Nebula-Admin-Key": ADMIN_KEY } }),
      context("tenants"),
    );

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe("GET");
    expect(init.body).toBeUndefined();
    expect((init.headers as Headers).get("X-Nebula-Admin-Key")).toBe(ADMIN_KEY);
  });

  it("answers 503 gateway_unreachable when the gateway cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    const response = await GET(new NextRequest("http://console.test/api/admin/tenants"), context("tenants"));

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
  });

  it("answers 503 gateway_unreachable for a write when the gateway cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    const response = await POST(
      new NextRequest("http://console.test/api/admin/tenants", { method: "POST", body: "{}" }),
      context("tenants"),
    );

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
  });

  it("logs why the gateway call failed before answering 503, so a bug is not mistaken for a network error", async () => {
    const cause = new TypeError("fetch failed");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(cause));

    const response = await GET(new NextRequest("http://console.test/api/admin/tenants"), context("tenants"));

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
    expect(consoleError).toHaveBeenCalledTimes(1);
    expect(consoleError).toHaveBeenCalledWith(expect.stringContaining("admin proxy"), cause);
  });

  it("logs neither the admin key nor the request body when the gateway call fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    await POST(
      new NextRequest("http://console.test/api/admin/tenants/acme/policy/simulate", {
        method: "POST",
        headers: { "X-Nebula-Admin-Key": ADMIN_KEY, "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_policy: { routing_mode_default: BODY_MARKER } }),
      }),
      context("tenants", "acme", "policy", "simulate"),
    );

    expect(consoleError).toHaveBeenCalledTimes(1);
    const logged = inspect(consoleError.mock.calls, { depth: 10 });
    expect(logged).not.toContain(ADMIN_KEY);
    expect(logged).not.toContain(BODY_MARKER);
  });

  it("does not log when the gateway answers, even with an error status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 500 })));

    await GET(new NextRequest("http://console.test/api/admin/tenants"), context("tenants"));

    expect(consoleError).not.toHaveBeenCalled();
  });
});
