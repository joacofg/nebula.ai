import { inspect } from "node:util";

import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";

// What a log line must never carry: the operator's admin key, and the prompt in the request body.
const ADMIN_KEY = "nb-admin-secret-7f3a";
const PROMPT = "prompt-marker-4c1e";

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

  it("logs neither the admin key nor the prompt when the gateway call fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    await POST(
      new NextRequest("http://console.test/api/playground/completions", {
        method: "POST",
        headers: { "X-Nebula-Admin-Key": ADMIN_KEY, "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_id: "acme", messages: [{ role: "user", content: PROMPT }] }),
      }),
    );

    expect(consoleError).toHaveBeenCalledTimes(1);
    const logged = inspect(consoleError.mock.calls, { depth: 10 });
    expect(logged).not.toContain(ADMIN_KEY);
    expect(logged).not.toContain(PROMPT);
  });

  it("does not log when the gateway answers", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 200 })));

    await POST(request());

    expect(consoleError).not.toHaveBeenCalled();
  });
});
