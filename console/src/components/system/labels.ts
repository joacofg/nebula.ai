/** Spanish labels for the gateway's enum codes; the raw code stays available as a title. */
const ROUTE_REASONS: Record<string, string> = {
  learned_router: "router aprendido",
  token_complexity: "heurística (complejidad)",
  cache_hit: "caché",
  explicit_premium_model: "modelo premium pedido",
  explicit_local_model: "modelo local pedido",
  local_provider_error_fallback: "fallback por error local",
  embeddings_request: "embeddings",
  hard_budget_downgrade: "degradado por presupuesto",
  calibrated_routing_disabled: "ruteo calibrado apagado",
  rate_limited: "límite de pedidos",
  fallback: "fallback",
};

const STATUSES: Record<string, string> = {
  completed: "completado",
  cache_hit: "caché",
  fallback_completed: "completado con fallback",
  policy_denied: "denegado por política",
  provider_error: "error del proveedor",
  rate_limited: "límite de pedidos",
};

const ROUTES: Record<string, string> = { cache: "caché", denied: "denegado" };

export function routeLabel(code: string) {
  return ROUTES[code] ?? code;
}

export function reasonLabel(code: string | null | undefined) {
  if (!code) {
    return "—";
  }
  return ROUTE_REASONS[code] ?? code;
}

export function statusLabel(code: string | null | undefined) {
  if (!code) {
    return "—";
  }
  return STATUSES[code] ?? code;
}

export function plural(n: number, one: string, many: string) {
  return `${n} ${n === 1 ? one : many}`;
}
