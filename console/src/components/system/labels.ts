/**
 * Spanish labels for the gateway's enum codes; the raw code stays available as a title.
 * Every function returns the raw code for one it does not know and a dash for none, never an
 * empty cell; only a table's own keys count as codes ("constructor" is just an unknown code).
 */
import { formatUsdText } from "@/lib/format";

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
  calibrated_routing_disabled: "ruteo automático apagado",
  rate_limited: "límite de pedidos",
  fallback: "fallback",
  // Not route reasons but the codes the calibration summary counts rows under; they share this
  // table because the summary words them with `reasonLabel`.
  explicit_model_override: "modelo explícito",
  policy_forced_routing: "ruteo forzado por la política",
  missing_route_signals: "sin señales de ruteo",
  degraded_replay_signals: "señales incompletas",
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

// How a request was scored (`route_mode` in the route signals).
const SCORE_MODES: Record<string, string> = {
  calibrated: "calibrado",
  degraded: "degradado",
};

// The policy simulation's approximation notes, by the code the gateway sends beside each text.
const APPROXIMATION_NOTES: Record<string, string> = {
  ledger_metadata_replay: "Se usan los metadatos guardados en el ledger, no el texto de los pedidos.",
  token_count_approximation: "Sin señales completas, la complejidad se aproxima con los tokens guardados.",
  pricing_estimate: "El costo usa los precios actuales; no se llama a ningún proveedor.",
  heuristic_fallback_rows:
    "Los pedidos sin probabilidades guardadas, o que el borrador saca del router aprendido, usan la heurística.",
};

// How a dependency matters to serving (`dependency_class`) and what its failure does (`serving_effect`).
const DEPENDENCY_CLASSES: Record<string, string> = {
  serving_critical: "crítica para servir",
  serving_optional: "opcional",
  metadata_only: "solo metadatos",
};

const SERVING_EFFECTS: Record<string, string> = {
  fail_closed: "bloquea pedidos",
  continuity_limited: "continuidad limitada",
  unaffected: "sin efecto",
};

// Why a dependency is in its state (`reason_code`): short, as the card shows the gateway's own detail too.
const HEALTH_REASONS: Record<string, string> = {
  governance_query_failed: "falló la consulta al almacén",
  governance_schema_incomplete: "esquema incompleto",
  governance_ready: "almacén conectado",
  semantic_cache_ready: "colección alcanzable",
  semantic_cache_unavailable: "caché no disponible",
  semantic_cache_collection_missing: "falta la colección",
  premium_provider_mock: "proveedor simulado",
  premium_provider_ready: "proveedor responde",
  premium_provider_unavailable: "proveedor no disponible",
  local_ollama_ready: "Ollama alcanzable",
  local_ollama_unavailable: "Ollama no disponible",
  retention_disabled: "retención desactivada",
  retention_idle: "sin limpiezas todavía",
  retention_running: "limpieza en curso",
  retention_failed: "falló la última limpieza",
  retention_ok: "última limpieza correcta",
};

// The retention lifecycle's last cleanup run (`last_status`).
const LAST_RUN_STATUSES: Record<string, string> = {
  idle: "sin corridas",
  running: "en curso",
  failed: "fallida",
  ok: "correcta",
};

// The cache insights the gateway builds, by `code`; their title and summary arrive in English.
const CACHE_INSIGHTS: Record<string, string> = {
  cache_runtime_ready: "Caché semántico en buen estado",
  cache_runtime_degraded: "Caché semántico degradado",
  cache_policy_disabled: "Caché semántico desactivado",
  cache_effectiveness_window: "Efectividad reciente del caché",
};

// The `label` of each evidence row of a cache insight.
const CACHE_EVIDENCE: Record<string, string> = {
  runtime_status: "Estado en runtime",
  cache_enabled: "Caché activado",
  cache_hits: "Aciertos",
  window_requests: "Pedidos en la ventana",
  avoided_premium_cost_usd: "Premium evitado",
};

// The governance values a ledger row carries.
const MESSAGE_TYPES: Record<string, string> = { chat: "Chat", embeddings: "Embeddings" };

const RETENTION_WINDOWS: Record<string, string> = {
  "24h": "24 horas",
  "7d": "7 días",
  "30d": "30 días",
  "90d": "90 días",
};

const MINIMIZATION_LEVELS: Record<string, string> = { standard: "estándar", strict: "estricta" };

const GOVERNANCE_SOURCES: Record<string, string> = { tenant_policy: "política del tenant" };

const SUPPRESSED_FIELDS: Record<string, string> = { route_signals: "señales de ruteo" };

// What a tenant's hard budget does when it is reached (`hard_budget_enforcement`).
const ENFORCEMENTS: Record<string, string> = { downgrade: "degradar a local", deny: "denegar" };

// How complex the heuristic found a prompt (`complexity_tier`).
const COMPLEXITIES: Record<string, string> = { low: "baja", medium: "media", high: "alta" };

// The denials the policy records, by the sentence the gateway writes (`denied=` in the policy outcome).
// Two carry something of their own (a model, amounts) and are read by pattern in `denialReasonLabel`.
const DENIALS: Record<string, string> = {
  "Request exceeds the tenant premium spend guardrail.": "El pedido supera el límite de costo por pedido",
  "Tenant policy requires premium-only routing.": "La política exige ruteo solo premium",
  "Tenant policy does not allow explicit premium routing.": "La política no permite pedir un modelo premium",
  "Tenant policy restricts this request to local routing only.": "La política restringe el pedido a ruteo solo local",
};

/** What a routing row says when it carries no mode of its own; the policy parity and the ledger detail share it. */
export const NO_SCORE_LABEL = "sin puntaje";

/** A routing score beside its mode: "puntaje 0.40". */
export function scoreLabel(score: string) {
  return `puntaje ${score}`;
}

/** A known code's label, the code itself when unknown, a dash when there is none. */
function lookup(labels: Record<string, string>, code: string | null | undefined) {
  if (!code) {
    return "—";
  }
  return Object.hasOwn(labels, code) ? labels[code] : code;
}

/** Where the answer came from: local / premium / cache / denied / embeddings. */
export function routeLabel(code: string | null | undefined) {
  return lookup(ROUTES, code);
}

/** The tenant's routing mode default: auto / local_only / premium_only. */
export function routingModeLabel(mode: string | null | undefined) {
  return lookup(ROUTING_MODES, mode);
}

/**
 * A policy outcome ("routing_mode=premium_only;denied=…;outcome_evidence=…") as the operator reads
 * it: the routing mode and whether it denied. The rest is the gateway's bookkeeping, never shown.
 * The gateway leaves `routing_mode=` out for auto, so a composite without it is "Automático"; an
 * empty outcome is no information, a dash.
 */
export function policyOutcomeLabel(outcome: string | null | undefined) {
  if (!outcome?.trim()) {
    return "—";
  }
  let mode = routingModeLabel("auto");
  let denied = false;
  for (const part of outcome.split(";")) {
    if (part.startsWith("routing_mode=")) {
      mode = routingModeLabel(part.slice("routing_mode=".length));
    } else if (part.startsWith("denied=")) {
      denied = true;
    }
  }
  return denied ? `${mode}, denegado` : mode;
}

/** What decides the tier: the learned router or the complexity heuristic. */
export function routerLabel(name: string | null | undefined) {
  return lookup(ROUTERS, name);
}

/** Health of the gateway, the cache and each dependency. */
export function runtimeStatusLabel(status: string | null | undefined) {
  return lookup(RUNTIME_STATUSES, status);
}

/** How a request was scored in the simulation's routing parity: calibrado / degradado. */
export function scoreModeLabel(mode: string | null | undefined) {
  return lookup(SCORE_MODES, mode);
}

/** A simulation note in Spanish by its code; a code it does not know shows the note's own text, a dash if it has none. */
export function approximationNoteLabel(code: string | null | undefined, text: string) {
  return code && Object.hasOwn(APPROXIMATION_NOTES, code) ? APPROXIMATION_NOTES[code] : text || "—";
}

/**
 * Why the policy denied a request, from the sentence the gateway recorded, keeping the model or the
 * amounts it carries; a sentence it does not know stays as written. The hard-budget sentence reaches
 * the ledger whole or cut at its first ";", so its amounts are optional.
 */
export function denialReasonLabel(text: string | null | undefined) {
  const model = text?.match(/^Premium model '(.+)' is not allowed for this tenant\.?$/);
  if (model) {
    return `Modelo premium '${model[1]}' no permitido para este tenant`;
  }
  if (text?.startsWith("Tenant hard budget limit reached")) {
    const amounts = text.match(/spent_usd=([^,)\s]+),\s*limit_usd=([^)\s]+)/);
    const reached = "Presupuesto duro alcanzado: ruteo premium bloqueado";
    return amounts
      ? `${reached} (gastado ${formatUsdText(amounts[1])}, límite ${formatUsdText(amounts[2])})`
      : reached;
  }
  return lookup(DENIALS, text);
}

/** A dependency's class: critical for serving, optional or metadata only. */
export function dependencyClassLabel(code: string | null | undefined) {
  return lookup(DEPENDENCY_CLASSES, code);
}

/** What a dependency's failure does to serving. */
export function servingEffectLabel(code: string | null | undefined) {
  return lookup(SERVING_EFFECTS, code);
}

/** Why a dependency reports its state. */
export function healthReasonLabel(code: string | null | undefined) {
  return lookup(HEALTH_REASONS, code);
}

/** The retention lifecycle's last cleanup run. */
export function lastRunStatusLabel(code: string | null | undefined) {
  return lookup(LAST_RUN_STATUSES, code);
}

/** A cache insight's title by its code; null for a code it does not know, so the caller keeps the gateway's own text. */
export function cacheInsightLabel(code: string | null | undefined) {
  return code && Object.hasOwn(CACHE_INSIGHTS, code) ? CACHE_INSIGHTS[code] : null;
}

/** The name of one evidence row of a cache insight. */
export function cacheEvidenceLabel(label: string | null | undefined) {
  return lookup(CACHE_EVIDENCE, label);
}

export function messageTypeLabel(code: string | null | undefined) {
  return lookup(MESSAGE_TYPES, code);
}

/** How long the evidence is kept: 24h / 7d / 30d / 90d. */
export function retentionWindowLabel(code: string | null | undefined) {
  return lookup(RETENTION_WINDOWS, code);
}

export function minimizationLabel(code: string | null | undefined) {
  return lookup(MINIMIZATION_LEVELS, code);
}

export function governanceSourceLabel(code: string | null | undefined) {
  return lookup(GOVERNANCE_SOURCES, code);
}

/** A metadata field the policy kept out of the ledger row. */
export function suppressedFieldLabel(code: string | null | undefined) {
  return lookup(SUPPRESSED_FIELDS, code);
}

/** What a tenant's hard budget does once it is reached. */
export function enforcementLabel(code: string | null | undefined) {
  return lookup(ENFORCEMENTS, code);
}

/** The complexity the heuristic saw in a prompt. */
export function complexityLabel(code: string | null | undefined) {
  return lookup(COMPLEXITIES, code);
}

export function reasonLabel(code: string | null | undefined) {
  return lookup(ROUTE_REASONS, code);
}

export function statusLabel(code: string | null | undefined) {
  return lookup(STATUSES, code);
}

export function plural(n: number, one: string, many: string) {
  return `${n} ${n === 1 ? one : many}`;
}
