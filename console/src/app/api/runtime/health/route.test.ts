import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

function request(adminKey?: string) {
  return new NextRequest("http://console.test/api/runtime/health", {
    headers: adminKey ? { "X-Nebula-Admin-Key": adminKey } : {},
  });
}

describe("runtime health proxy", () => {
  const consoleError = vi.spyOn(console, "error");

  beforeEach(() => {
    consoleError.mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    consoleError.mockReset();
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

  it.each([
    ["the session check", (cause: Error) => vi.fn().mockRejectedValue(cause)],
    [
      "the dependency check",
      (cause: Error) => vi.fn().mockResolvedValueOnce(new Response("{}", { status: 200 })).mockRejectedValueOnce(cause),
    ],
  ])("logs why %s failed before answering 503, so a bug is not mistaken for a network error", async (_name, stub) => {
    const cause = new TypeError("fetch failed");
    vi.stubGlobal("fetch", stub(cause));

    const response = await GET(request("nebula-admin-key"));

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: "gateway_unreachable" });
    expect(consoleError).toHaveBeenCalledTimes(1);
    expect(consoleError).toHaveBeenCalledWith(expect.stringContaining("runtime health proxy"), cause);
  });

  it("does not log when the admin key is missing or the gateway answers", async () => {
    await GET(request());
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 401 })));
    await GET(request("nebula-admin-key"));

    expect(consoleError).not.toHaveBeenCalled();
  });
});
