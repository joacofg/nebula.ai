import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET, POST } from "./route";

const context = (...path: string[]) => ({ params: Promise.resolve({ path }) });

describe("admin proxy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
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
});
