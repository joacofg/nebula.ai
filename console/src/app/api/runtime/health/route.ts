export async function GET() {
  const baseUrl = process.env.NEBULA_API_BASE_URL ?? "http://127.0.0.1:8000";
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
