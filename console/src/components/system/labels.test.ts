import { describe, expect, it } from "vitest";

import {
  approximationNoteLabel,
  cacheEvidenceLabel,
  cacheInsightLabel,
  complexityLabel,
  denialReasonLabel,
  dependencyClassLabel,
  enforcementLabel,
  governanceSourceLabel,
  healthReasonLabel,
  lastRunStatusLabel,
  messageTypeLabel,
  minimizationLabel,
  NO_SCORE_LABEL,
  plural,
  policyOutcomeLabel,
  reasonLabel,
  retentionWindowLabel,
  routeLabel,
  routerLabel,
  routingModeLabel,
  runtimeStatusLabel,
  scoreLabel,
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

  it("labels the codes the calibration summary counts rows under", () => {
    expect(reasonLabel("explicit_model_override")).toBe("modelo explícito");
    expect(reasonLabel("policy_forced_routing")).toBe("ruteo forzado por la política");
    expect(reasonLabel("missing_route_signals")).toBe("sin señales de ruteo");
    expect(reasonLabel("degraded_replay_signals")).toBe("señales incompletas");
    expect(reasonLabel("calibrated_routing_disabled")).toBe("ruteo automático apagado");
    expect(reasonLabel("rate_limited")).toBe("límite de pedidos");
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

describe("policyOutcomeLabel", () => {
  it.each([
    ["routing_mode=premium_only;denied=Request exceeds the tenant premium spend guardrail.", "Solo premium, denegado"],
    ["routing_mode=local_only;fallback=disabled;outcome_evidence=sufficient(route_mode=calibrated)", "Solo local"],
    ["routing_mode=auto;soft_budget=exceeded", "Automático"],
  ])("reads %s as %s", (outcome, label) => {
    expect(policyOutcomeLabel(outcome)).toBe(label);
  });

  it("reads a composite without a routing mode as Automático, because the gateway omits the mode for auto", () => {
    expect(policyOutcomeLabel("default")).toBe("Automático");
    expect(policyOutcomeLabel("soft_budget=exceeded;budget_action=downgraded_to_local")).toBe("Automático");
    expect(policyOutcomeLabel("denied=Request exceeds the tenant premium spend guardrail.")).toBe("Automático, denegado");
  });

  it("never shows the gateway's bookkeeping", () => {
    const label = policyOutcomeLabel(
      "routing_mode=local_only;calibrated_routing=disabled;cache=disabled;hard_budget=exceeded(limit_usd=1,spent_usd=2,enforcement=deny);outcome_evidence=degraded(eligible=1)",
    );
    expect(label).toBe("Solo local");
  });

  it("returns an unknown routing mode as it came", () => {
    expect(policyOutcomeLabel("routing_mode=round_robin")).toBe("round_robin");
  });

  it("shows a dash when there is no outcome to read, never an empty cell", () => {
    expect(policyOutcomeLabel("")).toBe("—");
    expect(policyOutcomeLabel("   ")).toBe("—");
    expect(policyOutcomeLabel(null)).toBe("—");
    expect(policyOutcomeLabel(undefined)).toBe("—");
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
    expect(cacheEvidenceLabel("cache_enabled")).toBe("Caché activado");
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

describe("denialReasonLabel", () => {
  it("words each denial the gateway can record, keeping the model and the amounts they carry", () => {
    expect(denialReasonLabel("Premium model 'openai/gpt-4o' is not allowed for this tenant.")).toBe(
      "Modelo premium 'openai/gpt-4o' no permitido para este tenant",
    );
    expect(denialReasonLabel("Request exceeds the tenant premium spend guardrail.")).toBe(
      "El pedido supera el límite de costo por pedido",
    );
    expect(
      denialReasonLabel("Tenant hard budget limit reached; premium routing is blocked (spent_usd=0.1, limit_usd=0.05)."),
    ).toBe("Presupuesto duro alcanzado: ruteo premium bloqueado (gastado USD 0.1000, límite USD 0.0500)");
    expect(denialReasonLabel("Tenant policy requires premium-only routing.")).toBe(
      "La política exige ruteo solo premium",
    );
    expect(denialReasonLabel("Tenant policy does not allow explicit premium routing.")).toBe(
      "La política no permite pedir un modelo premium",
    );
    expect(denialReasonLabel("Tenant policy restricts this request to local routing only.")).toBe(
      "La política restringe el pedido a ruteo solo local",
    );
  });

  it("words a hard-budget denial cut before its amounts, as the policy outcome keeps it", () => {
    expect(denialReasonLabel("Tenant hard budget limit reached")).toBe(
      "Presupuesto duro alcanzado: ruteo premium bloqueado",
    );
  });

  it("keeps an amount that is not a number as written", () => {
    expect(
      denialReasonLabel("Tenant hard budget limit reached; premium routing is blocked (spent_usd=0.1, limit_usd=unknown)."),
    ).toBe("Presupuesto duro alcanzado: ruteo premium bloqueado (gastado USD 0.1000, límite USD unknown)");
  });

  it("keeps a denial it does not know as the gateway wrote it", () => {
    expect(denialReasonLabel("Something new was denied.")).toBe("Something new was denied.");
    expect(denialReasonLabel("Premium model 'x' is not allowed for another reason.")).toBe(
      "Premium model 'x' is not allowed for another reason.",
    );
    expect(denialReasonLabel("")).toBe("—");
  });
});

describe("routing score words", () => {
  it("words a missing score and a score the way the policy parity and the ledger detail share", () => {
    expect(NO_SCORE_LABEL).toBe("sin puntaje");
    expect(scoreLabel("0.40")).toBe("puntaje 0.40");
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
