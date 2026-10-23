/**
 * Spanish labels for the gateway's enum codes; the raw code stays available as a title.
 * Every function returns the raw code for one it does not know, never an empty cell.
 */
const ROUTE_REASONS: Record<string, string> = {
  learned_router: "router aprendido",
  token_complexity: "heurística por complejidad",
  cache_hit: "caché",
  explicit_premium_model: "modelo premium pedido",
  explicit_local_model: "modelo local pedido",
  local_provider_error_fallback: "fallback por error local",
  local_provider_error_fallback_blocked: "fallback bloqueado por política",
  policy_local_only: "política: solo local",
  policy_premium_only: "política: solo premium",
  embeddings_request: "embeddings",
  embeddings_direct: "embeddings directos",
  embeddings_validation_error: "embeddings: pedido inválido",
  embeddings_upstream_error: "embeddings: error del proveedor",
  embeddings_empty_result: "embeddings: resultado vacío",
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
  client_disconnected: "cortado por el cliente",
};

const ROUTES: Record<string, string> = {
  local: "Local",
  premium: "Premium",
  cache: "Caché",
  denied: "Denegado",
  embeddings: "Embeddings",
};

const ROUTING_MODES: Record<string, string> = {
  auto: "Automático",
  local_only: "Solo local",
  premium_only: "Solo premium",
};

const ROUTERS: Record<string, string> = {
  learned_router: "Router aprendido",
  token_complexity: "Heurística por complejidad",
};

const RUNTIME_STATUSES: Record<string, string> = {
  ready: "Listo",
  degraded: "Degradado",
  not_ready: "No listo",
  recovering: "Recuperándose",
  disabled: "Desactivado",
  unknown: "Desconocido",
};

/** Where the answer came from: local / premium / cache / denied / embeddings. */
export function routeLabel(code: string) {
  return ROUTES[code] ?? code;
}

/** The tenant's routing mode default: auto / local_only / premium_only. */
export function routingModeLabel(mode: string) {
  return ROUTING_MODES[mode] ?? mode;
}

/** What decides the tier: the learned router or the complexity heuristic. */
export function routerLabel(name: string) {
  return ROUTERS[name] ?? name;
}

/** Health of the gateway, the cache and each dependency. */
export function runtimeStatusLabel(status: string) {
  return RUNTIME_STATUSES[status] ?? status;
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
