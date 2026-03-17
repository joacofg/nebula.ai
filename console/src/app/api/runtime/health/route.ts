import type { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const baseUrl = process.env.NEBULA_API_BASE_URL ?? "http://127.0.0.1:8000";
  const adminKey = request.headers.get("X-Nebula-Admin-Key") ?? "";

  if (!adminKey) {
    return Response.json({ detail: "Nebula admin key missing." }, { status: 401 });
  }

  const sessionResponse = await fetch(new URL("/v1/admin/session", baseUrl), {
    headers: {
      "X-Nebula-Admin-Key": adminKey,
    },
    cache: "no-store",
  });
  if (!sessionResponse.ok) {
    return new Response(await sessionResponse.arrayBuffer(), {
      status: sessionResponse.status,
      headers: {
        "Content-Type": sessionResponse.headers.get("Content-Type") ?? "application/json",
      },
    });
  }

  const response = await fetch(new URL("/health/dependencies", baseUrl), {
    cache: "no-store",
  });

  return new Response(await response.arrayBuffer(), {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
}
