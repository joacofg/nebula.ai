import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";

function request() {
  return new NextRequest("http://console.test/api/playground/completions", { method: "POST", body: "{}" });
}

describe("playground proxy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("forwards the gateway answer and the routing headers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("{}", { status: 200, headers: { "X-Nebula-Route-Target": "local" } }),
      ),
    );

    const response = await POST(request());

    expect(response.status).toBe(200);
    expect(response.headers.get("X-Nebula-Route-Target")).toBe("local");
  });

  it("answers 503 gateway_unreachable when the gateway cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    const response = await POST(request());

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
  });
});
