import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";

function request() {
  return new NextRequest("http://console.test/api/playground/completions", { method: "POST", body: "{}" });
}

describe("playground proxy", () => {
  const consoleError = vi.spyOn(console, "error");

  beforeEach(() => {
    consoleError.mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    consoleError.mockReset();
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

  it("logs why the gateway call failed before answering 503, so a bug is not mistaken for a network error", async () => {
    const cause = new TypeError("fetch failed");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(cause));

    const response = await POST(request());

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
    expect(consoleError).toHaveBeenCalledTimes(1);
    expect(consoleError).toHaveBeenCalledWith(expect.stringContaining("playground proxy"), cause);
  });

  it("does not log when the gateway answers", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 200 })));

    await POST(request());

    expect(consoleError).not.toHaveBeenCalled();
  });
});
