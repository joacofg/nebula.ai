import { describe, expect, it } from "vitest";

import {
  approximationNoteLabel,
  plural,
  reasonLabel,
  routeLabel,
  routerLabel,
  routingModeLabel,
  runtimeStatusLabel,
  scoreModeLabel,
  statusLabel,
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
});
