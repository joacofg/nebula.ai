import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

function request(adminKey?: string) {
  return new NextRequest("http://console.test/api/runtime/health", {
    headers: adminKey ? { "X-Nebula-Admin-Key": adminKey } : {},
  });
}

describe("runtime health proxy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("answers 401 when the admin key is missing", async () => {
    const response = await GET(request());

    expect(response.status).toBe(401);
  });

  it("answers 503 gateway_unreachable when the session check cannot reach the gateway", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    const response = await GET(request("nebula-admin-key"));

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
  });

  it("answers 503 gateway_unreachable when the dependency check cannot reach the gateway", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response("{}", { status: 200 }))
        .mockRejectedValueOnce(new TypeError("fetch failed")),
    );

    const response = await GET(request("nebula-admin-key"));

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
  });
});
