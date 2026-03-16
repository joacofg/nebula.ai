import type { NextRequest } from "next/server";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function buildUpstreamUrl(path: string[]) {
  const baseUrl = process.env.NEBULA_API_BASE_URL ?? "http://127.0.0.1:8000";
  return new URL(`/v1/admin/${path.join("/")}`, baseUrl);
}

async function proxyRequest(request: NextRequest, path: string[]) {
  const upstreamUrl = buildUpstreamUrl(path);
  request.nextUrl.searchParams.forEach((value, key) => {
    upstreamUrl.searchParams.set(key, value);
  });

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  const response = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  response.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  return new Response(await response.arrayBuffer(), {
    status: response.status,
    headers: responseHeaders,
  });
}

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, (await context.params).path);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, (await context.params).path);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, (await context.params).path);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, (await context.params).path);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, (await context.params).path);
}
