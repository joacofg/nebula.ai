import { describe, expect, it } from "vitest";

import {
  numberText,
  parsePolicyNumber,
  policyFormChanged,
  validatePolicyForm,
  type PolicyFormField,
  type PolicyFormState,
} from "@/components/policy/policy-validation";

const validState: PolicyFormState = {
  routingModeDefault: "auto",
  calibratedRoutingEnabled: true,
  fallbackEnabled: true,
  semanticCacheEnabled: true,
  semanticCacheSimilarityThreshold: "0.9",
  semanticCacheMaxEntryAgeHours: "168",
  allowedPremiumModels: ["openai/gpt-4o-mini"],
  maxPremiumCostPerRequest: "",
  hardBudgetLimitUsd: "",
  hardBudgetEnforcement: "downgrade",
  softBudgetUsd: "",
  evidenceRetentionWindow: "30d",
  metadataMinimizationLevel: "standard",
  routingQualityTarget: "0.90",
  rateLimitRequestsPerMinute: "",
};

describe("parsePolicyNumber", () => {
  it("reads a decimal point or a decimal comma", () => {
    expect(parsePolicyNumber("10.5")).toBe(10.5);
    expect(parsePolicyNumber("10,5")).toBe(10.5);
    expect(parsePolicyNumber("0,82")).toBe(0.82);
    expect(parsePolicyNumber(".5")).toBe(0.5);
    expect(parsePolicyNumber("25")).toBe(25);
  });

  it("trims the text and reads an empty one as no value", () => {
    expect(parsePolicyNumber(" 3 ")).toBe(3);
    expect(parsePolicyNumber("")).toBeNull();
    expect(parsePolicyNumber("   ")).toBeNull();
  });

  it("never reads a typo as a number or as no value", () => {
    for (const text of ["abc", "1,2,3", "1.000,5", "10.", "1e3", "Infinity", "NaN", "12abc", "--1", "1 000", "+3", "0x10"]) {
      expect(parsePolicyNumber(text), text).toBe("invalid");
    }
  });

  it("reads a negative number as a number so the range check can name it", () => {
    expect(parsePolicyNumber("-2")).toBe(-2);
    expect(Object.is(parsePolicyNumber("-0"), 0)).toBe(true);
  });

  it("rejects a number too large to be finite", () => {
    expect(parsePolicyNumber("9".repeat(400))).toBe("invalid");
  });
});

describe("numberText", () => {
  it("writes a stored number back as field text without exponent notation", () => {
    expect(numberText(10.5)).toBe("10.5");
    expect(numberText(168)).toBe("168");
    expect(numberText(null)).toBe("");
    expect(numberText(undefined)).toBe("");
    expect(numberText(1e-7)).toBe("0.0000001");
    expect(parsePolicyNumber(numberText(1e-7))).toBe(1e-7);
  });
});

describe("policyFormChanged", () => {
  it("compares what the numbers mean, not how they are typed", () => {
    expect(policyFormChanged(validState, { ...validState })).toBe(false);
    expect(policyFormChanged({ ...validState, routingQualityTarget: "0.9" }, validState)).toBe(false);
    expect(policyFormChanged({ ...validState, softBudgetUsd: "10,5" }, { ...validState, softBudgetUsd: "10.5" })).toBe(false);
    expect(policyFormChanged({ ...validState, rateLimitRequestsPerMinute: " 3 " }, { ...validState, rateLimitRequestsPerMinute: "3" })).toBe(false);
    expect(policyFormChanged({ ...validState, hardBudgetLimitUsd: "   " }, validState)).toBe(false);
  });

  it("sees a different number, a typo and any other field", () => {
    expect(policyFormChanged({ ...validState, routingQualityTarget: "0.91" }, validState)).toBe(true);
    expect(policyFormChanged({ ...validState, softBudgetUsd: "abc" }, validState)).toBe(true);
    expect(policyFormChanged({ ...validState, softBudgetUsd: "abc" }, { ...validState, softBudgetUsd: "abd" })).toBe(true);
    expect(policyFormChanged({ ...validState, fallbackEnabled: false }, validState)).toBe(true);
    expect(policyFormChanged({ ...validState, allowedPremiumModels: [] }, validState)).toBe(true);
  });
});

describe("validatePolicyForm", () => {
  it("builds the payload from a valid form", () => {
    const { errors, payload } = validatePolicyForm({
      ...validState,
      maxPremiumCostPerRequest: "0,5",
      hardBudgetLimitUsd: " 25 ",
      softBudgetUsd: "10,5",
      rateLimitRequestsPerMinute: " 3 ",
      semanticCacheSimilarityThreshold: "0,82",
      semanticCacheMaxEntryAgeHours: "48",
      routingQualityTarget: "0,9",
    });

    expect(errors).toEqual({});
    expect(payload).toEqual({
      routing_mode_default: "auto",
      calibrated_routing_enabled: true,
      fallback_enabled: true,
      semantic_cache_enabled: true,
      semantic_cache_similarity_threshold: 0.82,
      semantic_cache_max_entry_age_hours: 48,
      allowed_premium_models: ["openai/gpt-4o-mini"],
      max_premium_cost_per_request: 0.5,
      hard_budget_limit_usd: 25,
      hard_budget_enforcement: "downgrade",
      soft_budget_usd: 10.5,
      evidence_retention_window: "30d",
      metadata_minimization_level: "standard",
      routing_quality_target: 0.9,
      rate_limit_requests_per_minute: 3,
    });
  });

  it("reads empty optional fields as no limit", () => {
    const { payload } = validatePolicyForm(validState);

    expect(payload).toMatchObject({
      max_premium_cost_per_request: null,
      hard_budget_limit_usd: null,
      hard_budget_enforcement: null,
      soft_budget_usd: null,
      rate_limit_requests_per_minute: null,
    });
  });

  it("keeps the enforcement choice once a hard budget is set", () => {
    const { payload } = validatePolicyForm({ ...validState, hardBudgetLimitUsd: "5", hardBudgetEnforcement: "deny" });

    expect(payload).toMatchObject({ hard_budget_limit_usd: 5, hard_budget_enforcement: "deny" });
  });

  it("names 'Número inválido.' for a typo in any optional number, never 'no limit'", () => {
    for (const field of [
      "maxPremiumCostPerRequest",
      "hardBudgetLimitUsd",
      "softBudgetUsd",
      "rateLimitRequestsPerMinute",
    ] as const) {
      const { errors, payload } = validatePolicyForm({ ...validState, [field]: "abc" });

      expect(errors[field], field).toBe("Número inválido.");
      expect(payload, field).toBeNull();
    }
  });

  it("rejects a negative amount in dollars", () => {
    const { errors, payload } = validatePolicyForm({ ...validState, hardBudgetLimitUsd: "-1" });

    expect(errors.hardBudgetLimitUsd).toBe("No puede ser negativo.");
    expect(payload).toBeNull();
  });

  it("keeps the rate limit to a whole number between 1 and 100000", () => {
    const message = "El límite tiene que ser un entero entre 1 y 100000 pedidos por minuto.";
    for (const text of ["0", "2.5", "10,5", "100001", "-3"]) {
      const { errors } = validatePolicyForm({ ...validState, rateLimitRequestsPerMinute: text });

      expect(errors.rateLimitRequestsPerMinute, text).toBe(message);
    }
    for (const text of ["1", "100000", " 3 "]) {
      expect(validatePolicyForm({ ...validState, rateLimitRequestsPerMinute: text }).errors).toEqual({});
    }
  });

  it("keeps the similarity threshold between 0 and 1 and never reads empty as 0", () => {
    const message = "El umbral de similitud tiene que estar entre 0 y 1.";
    for (const text of ["1.2", "-0.1", "", "abc"]) {
      const { errors } = validatePolicyForm({ ...validState, semanticCacheSimilarityThreshold: text });

      expect(errors.semanticCacheSimilarityThreshold, text).toBe(text === "abc" ? "Número inválido." : message);
    }
    expect(validatePolicyForm({ ...validState, semanticCacheSimilarityThreshold: "0" }).errors).toEqual({});
    expect(validatePolicyForm({ ...validState, semanticCacheSimilarityThreshold: "1" }).errors).toEqual({});
  });

  it("keeps the maximum age to a whole number of hours between 1 and 720", () => {
    const message = "La antigüedad máxima tiene que ser un entero entre 1 y 720 horas.";
    for (const text of ["0", "721", "48,5", ""]) {
      const { errors } = validatePolicyForm({ ...validState, semanticCacheMaxEntryAgeHours: text });

      expect(errors.semanticCacheMaxEntryAgeHours, text).toBe(message);
    }
    expect(validatePolicyForm({ ...validState, semanticCacheMaxEntryAgeHours: "720" }).errors).toEqual({});
  });

  it("keeps the quality target between 0.75 and 1.00", () => {
    const message = "El objetivo de calidad tiene que estar entre 0.75 y 1.00.";
    for (const text of ["0.7", "0.74", "1.01", "0.5", ""]) {
      const { errors } = validatePolicyForm({ ...validState, routingQualityTarget: text });

      expect(errors.routingQualityTarget, text).toBe(message);
    }
    expect(validatePolicyForm({ ...validState, routingQualityTarget: "abc" }).errors.routingQualityTarget).toBe(
      "Número inválido.",
    );
    for (const text of ["0.75", "1", "1,00", "0.95"]) {
      expect(validatePolicyForm({ ...validState, routingQualityTarget: text }).errors, text).toEqual({});
    }
  });

  it("asks for at least one premium model", () => {
    const { errors, payload } = validatePolicyForm({ ...validState, allowedPremiumModels: [] });

    expect(errors.allowedPremiumModels).toBe("Elegir al menos un modelo premium.");
    expect(payload).toBeNull();
  });

  it("does not validate a field the form does not show, and leaves it out of the payload", () => {
    const hidden = new Set<PolicyFormField>(["routingQualityTarget", "rateLimitRequestsPerMinute", "allowedPremiumModels"]);

    const { errors, payload } = validatePolicyForm(
      { ...validState, routingQualityTarget: "0.60", rateLimitRequestsPerMinute: "abc", allowedPremiumModels: [] },
      hidden,
    );

    expect(errors).toEqual({});
    expect(payload).not.toBeNull();
    expect(payload).not.toHaveProperty("routing_quality_target");
    expect(payload).not.toHaveProperty("rate_limit_requests_per_minute");
    expect(payload).not.toHaveProperty("allowed_premium_models");
    expect(payload).toMatchObject({ semantic_cache_max_entry_age_hours: 168, routing_mode_default: "auto" });
  });

  it("still validates the fields it shows when others are hidden", () => {
    const hidden = new Set<PolicyFormField>(["routingQualityTarget"]);

    const { errors, payload } = validatePolicyForm(
      { ...validState, routingQualityTarget: "0.60", rateLimitRequestsPerMinute: "abc" },
      hidden,
    );

    expect(Object.keys(errors)).toEqual(["rateLimitRequestsPerMinute"]);
    expect(payload).toBeNull();
  });

  it("reports every invalid field at once", () => {
    const { errors } = validatePolicyForm({
      ...validState,
      rateLimitRequestsPerMinute: "abc",
      softBudgetUsd: "x",
      routingQualityTarget: "0.2",
    });

    expect(Object.keys(errors).sort()).toEqual(["rateLimitRequestsPerMinute", "routingQualityTarget", "softBudgetUsd"]);
  });
});
