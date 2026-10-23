import { describe, expect, it } from "vitest";

import {
  approximationNoteLabel,
  cacheEvidenceLabel,
  cacheInsightLabel,
  complexityLabel,
  dependencyClassLabel,
  enforcementLabel,
  governanceSourceLabel,
  healthReasonLabel,
  lastRunStatusLabel,
  messageTypeLabel,
  minimizationLabel,
  plural,
  reasonLabel,
  retentionWindowLabel,
  routeLabel,
  routerLabel,
  routingModeLabel,
  runtimeStatusLabel,
  scoreModeLabel,
  servingEffectLabel,
  statusLabel,
  suppressedFieldLabel,
} from "@/components/system/labels";

describe("labels", () => {
  it("maps known codes and passes unknown ones through", () => {
    expect(reasonLabel("learned_router")).toBe("router aprendido");
    expect(reasonLabel("local_provider_error_fallback_blocked")).toBe("fallback bloqueado por política");
    expect(reasonLabel("something_new")).toBe("something_new");
    expect(reasonLabel(null)).toBe("—");
    expect(statusLabel("provider_error")).toBe("error del proveedor");
    expect(statusLabel("fallback_completed")).toBe("completado con fallback");
    expect(statusLabel("client_disconnected")).toBe("cortado por el cliente");
  });

  it("labels the reasons a policy or an embeddings request leaves in the ledger", () => {
    expect(reasonLabel("policy_local_only")).toBe("política: solo local");
    expect(reasonLabel("policy_premium_only")).toBe("política: solo premium");
    expect(reasonLabel("embeddings_direct")).toBe("embeddings directos");
    expect(reasonLabel("embeddings_validation_error")).toBe("embeddings: pedido inválido");
    expect(reasonLabel("embeddings_upstream_error")).toBe("embeddings: error del proveedor");
    expect(reasonLabel("embeddings_empty_result")).toBe("embeddings: resultado vacío");
    expect(reasonLabel("embeddings_something_new")).toBe("embeddings_something_new");
  });

  it("names the heuristic the same way as a reason and as a router", () => {
    expect(reasonLabel("token_complexity")).toBe("heurística por complejidad");
    expect(routerLabel("token_complexity")).toBe("Heurística por complejidad");
  });

  it("pluralizes", () => {
    expect(plural(1, "recomendación", "recomendaciones")).toBe("1 recomendación");
    expect(plural(3, "recomendación", "recomendaciones")).toBe("3 recomendaciones");
  });
});

describe("every label function", () => {
  const labelFunctions = [
    ["reasonLabel", reasonLabel],
    ["statusLabel", statusLabel],
    ["routeLabel", routeLabel],
    ["routingModeLabel", routingModeLabel],
    ["routerLabel", routerLabel],
    ["runtimeStatusLabel", runtimeStatusLabel],
    ["scoreModeLabel", scoreModeLabel],
    ["dependencyClassLabel", dependencyClassLabel],
    ["servingEffectLabel", servingEffectLabel],
    ["healthReasonLabel", healthReasonLabel],
    ["lastRunStatusLabel", lastRunStatusLabel],
    ["cacheEvidenceLabel", cacheEvidenceLabel],
    ["messageTypeLabel", messageTypeLabel],
    ["retentionWindowLabel", retentionWindowLabel],
    ["minimizationLabel", minimizationLabel],
    ["governanceSourceLabel", governanceSourceLabel],
    ["suppressedFieldLabel", suppressedFieldLabel],
    ["enforcementLabel", enforcementLabel],
    ["complexityLabel", complexityLabel],
  ] as const;

  it.each(labelFunctions)("%s returns an unknown code as it came", (_name, label) => {
    expect(label("something_new")).toBe("something_new");
  });

  it.each(labelFunctions)("%s shows a dash for an empty code, never an empty cell", (_name, label) => {
    expect(label("")).toBe("—");
  });

  it.each(labelFunctions)("%s does not read inherited object properties as codes", (_name, label) => {
    for (const code of ["constructor", "toString", "__proto__", "hasOwnProperty"]) {
      expect(label(code)).toBe(code);
    }
  });
});

describe("routeLabel", () => {
  it.each([
    ["local", "Local"],
    ["premium", "Premium"],
    ["cache", "Caché"],
    ["denied", "Denegado"],
    ["embeddings", "Embeddings"],
  ])("labels %s as %s", (code, label) => {
    expect(routeLabel(code)).toBe(label);
  });

  it("returns an unknown route as it came, never an empty cell", () => {
    expect(routeLabel("something_new")).toBe("something_new");
  });
});

describe("routingModeLabel", () => {
  it.each([
    ["auto", "Automático"],
    ["local_only", "Solo local"],
    ["premium_only", "Solo premium"],
  ])("labels %s as %s", (mode, label) => {
    expect(routingModeLabel(mode)).toBe(label);
  });

  it("returns an unknown mode as it came", () => {
    expect(routingModeLabel("round_robin")).toBe("round_robin");
  });
});

describe("routerLabel", () => {
  it("names the learned router and the heuristic", () => {
    expect(routerLabel("learned_router")).toBe("Router aprendido");
    expect(routerLabel("token_complexity")).toBe("Heurística por complejidad");
  });

  it("returns an unknown router as it came", () => {
    expect(routerLabel("v2_experimental")).toBe("v2_experimental");
  });
});

describe("runtimeStatusLabel", () => {
  it.each([
    ["ready", "Listo"],
    ["degraded", "Degradado"],
    ["not_ready", "No listo"],
    ["recovering", "Recuperándose"],
    ["disabled", "Desactivado"],
    ["unknown", "Desconocido"],
  ])("labels %s as %s", (status, label) => {
    expect(runtimeStatusLabel(status)).toBe(label);
  });

  it("returns an unknown status as it came", () => {
    expect(runtimeStatusLabel("on_fire")).toBe("on_fire");
  });
});

describe("dependency labels", () => {
  it.each([
    ["serving_critical", "crítica para servir"],
    ["serving_optional", "opcional"],
    ["metadata_only", "solo metadatos"],
  ])("labels the class %s as %s", (code, label) => {
    expect(dependencyClassLabel(code)).toBe(label);
  });

  it.each([
    ["fail_closed", "bloquea pedidos"],
    ["continuity_limited", "continuidad limitada"],
    ["unaffected", "sin efecto"],
  ])("labels the serving effect %s as %s", (code, label) => {
    expect(servingEffectLabel(code)).toBe(label);
  });

  it("says in Spanish every reason a dependency reports", () => {
    for (const code of [
      "governance_query_failed",
      "governance_schema_incomplete",
      "governance_ready",
      "semantic_cache_ready",
      "semantic_cache_unavailable",
      "semantic_cache_collection_missing",
      "premium_provider_mock",
      "premium_provider_ready",
      "premium_provider_unavailable",
      "local_ollama_ready",
      "local_ollama_unavailable",
      "retention_disabled",
      "retention_idle",
      "retention_running",
      "retention_failed",
      "retention_ok",
    ]) {
      expect(healthReasonLabel(code), code).not.toBe(code);
    }
    expect(healthReasonLabel("semantic_cache_unavailable")).toBe("caché no disponible");
    expect(healthReasonLabel("governance_query_failed")).toBe("falló la consulta al almacén");
  });

  it.each([
    ["idle", "sin corridas"],
    ["running", "en curso"],
    ["failed", "fallida"],
    ["ok", "correcta"],
  ])("labels the last retention run %s as %s", (code, label) => {
    expect(lastRunStatusLabel(code)).toBe(label);
  });
});

describe("cache labels", () => {
  it("titles each insight the gateway can send by its code", () => {
    expect(cacheInsightLabel("cache_runtime_ready")).toBe("Caché semántico en buen estado");
    expect(cacheInsightLabel("cache_runtime_degraded")).toBe("Caché semántico degradado");
    expect(cacheInsightLabel("cache_policy_disabled")).toBe("Caché semántico desactivado");
    expect(cacheInsightLabel("cache_effectiveness_window")).toBe("Efectividad reciente del caché");
  });

  it("answers nothing for an insight it does not know, so the caller keeps the gateway's own text", () => {
    expect(cacheInsightLabel("cache-health-watch")).toBeNull();
    expect(cacheInsightLabel("")).toBeNull();
    expect(cacheInsightLabel("constructor")).toBeNull();
  });

  it("names the evidence rows of an insight", () => {
    expect(cacheEvidenceLabel("runtime_status")).toBe("Estado en runtime");
    expect(cacheEvidenceLabel("cache_enabled")).toBe("Caché activada");
    expect(cacheEvidenceLabel("cache_hits")).toBe("Aciertos");
    expect(cacheEvidenceLabel("window_requests")).toBe("Pedidos en la ventana");
    expect(cacheEvidenceLabel("avoided_premium_cost_usd")).toBe("Premium evitado");
  });
});

describe("ledger detail labels", () => {
  it("words the governance values of a ledger row", () => {
    expect(messageTypeLabel("chat")).toBe("Chat");
    expect(messageTypeLabel("embeddings")).toBe("Embeddings");
    expect(retentionWindowLabel("24h")).toBe("24 horas");
    expect(retentionWindowLabel("7d")).toBe("7 días");
    expect(retentionWindowLabel("30d")).toBe("30 días");
    expect(retentionWindowLabel("90d")).toBe("90 días");
    expect(minimizationLabel("standard")).toBe("estándar");
    expect(minimizationLabel("strict")).toBe("estricta");
    expect(governanceSourceLabel("tenant_policy")).toBe("política del tenant");
    expect(suppressedFieldLabel("route_signals")).toBe("señales de ruteo");
  });

  it("words the budget enforcement and the complexity the router saw", () => {
    expect(enforcementLabel("downgrade")).toBe("degradar a local");
    expect(enforcementLabel("deny")).toBe("denegar");
    expect(complexityLabel("low")).toBe("baja");
    expect(complexityLabel("medium")).toBe("media");
    expect(complexityLabel("high")).toBe("alta");
  });
});

describe("scoreModeLabel", () => {
  it("labels how a request was scored", () => {
    expect(scoreModeLabel("calibrated")).toBe("calibrado");
    expect(scoreModeLabel("degraded")).toBe("degradado");
  });
});

describe("approximationNoteLabel", () => {
  it.each([
    ["ledger_metadata_replay", "Se usan los metadatos guardados en el ledger, no el texto de los pedidos."],
    ["token_count_approximation", "Sin señales completas, la complejidad se aproxima con los tokens guardados."],
    ["pricing_estimate", "El costo usa los precios actuales; no se llama a ningún proveedor."],
    ["heuristic_fallback_rows", "Los pedidos sin probabilidades guardadas, o que el borrador saca del router aprendido, usan la heurística."],
  ])("words %s in Spanish", (code, label) => {
    expect(approximationNoteLabel(code, "English text from the API")).toBe(label);
  });

  it("shows the note's own text for a code it does not know or none", () => {
    expect(approximationNoteLabel("something_new", "Something new happened.")).toBe("Something new happened.");
    expect(approximationNoteLabel(undefined, "Plain note.")).toBe("Plain note.");
    expect(approximationNoteLabel("constructor", "Plain note.")).toBe("Plain note.");
  });

  it("shows a dash, never an empty line, for an unknown code with no text", () => {
    expect(approximationNoteLabel("something_new", "")).toBe("—");
    expect(approximationNoteLabel(undefined, "")).toBe("—");
    expect(approximationNoteLabel("pricing_estimate", "")).toBe("El costo usa los precios actuales; no se llama a ningún proveedor.");
  });
});

describe("the reason a tenant's automatic routing is off", () => {
  it("is named like the Policy checkbox that turns it off", () => {
    expect(reasonLabel("calibrated_routing_disabled")).toBe("ruteo automático apagado");
  });
});
