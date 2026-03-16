import type { NextRequest } from "next/server";

const RESPONSE_HEADERS = [
  "X-Request-ID",
  "X-Nebula-Tenant-ID",
  "X-Nebula-Route-Target",
  "X-Nebula-Route-Reason",
  "X-Nebula-Provider",
  "X-Nebula-Cache-Hit",
  "X-Nebula-Fallback-Used",
  "X-Nebula-Policy-Mode",
  "X-Nebula-Policy-Outcome",
];

function buildUpstreamUrl() {
  const baseUrl = process.env.NEBULA_API_BASE_URL ?? "http://127.0.0.1:8000";
  return new URL("/v1/admin/playground/completions", baseUrl);
}

export async function POST(request: NextRequest) {
  const upstream = await fetch(buildUpstreamUrl(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Nebula-Admin-Key": request.headers.get("X-Nebula-Admin-Key") ?? "",
    },
    body: await request.text(),
    cache: "no-store",
  });

  const headers = new Headers({
    "Content-Type": upstream.headers.get("Content-Type") ?? "application/json",
  });
  for (const header of RESPONSE_HEADERS) {
    const value = upstream.headers.get(header);
    if (value !== null) {
      headers.set(header, value);
    }
  }

  return new Response(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers,
  });
}
