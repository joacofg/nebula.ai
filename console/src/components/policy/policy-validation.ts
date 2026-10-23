import type { TenantPolicy } from "@/lib/admin-api";
import { TARGET_MAX, TARGET_MIN, formatTarget } from "@/lib/quality-target";

/** What the Policy form holds: numbers are the operator's text until they are validated. */
export type PolicyFormState = {
  routingModeDefault: TenantPolicy["routing_mode_default"];
  calibratedRoutingEnabled: boolean;
  fallbackEnabled: boolean;
  semanticCacheEnabled: boolean;
  semanticCacheSimilarityThreshold: string;
  semanticCacheMaxEntryAgeHours: string;
  allowedPremiumModels: string[];
  maxPremiumCostPerRequest: string;
  hardBudgetLimitUsd: string;
  hardBudgetEnforcement: NonNullable<TenantPolicy["hard_budget_enforcement"]>;
  softBudgetUsd: string;
  evidenceRetentionWindow: TenantPolicy["evidence_retention_window"];
  metadataMinimizationLevel: TenantPolicy["metadata_minimization_level"];
  routingQualityTarget: string;
  rateLimitRequestsPerMinute: string;
};

export type PolicyFormField = keyof PolicyFormState;

/** One message per invalid field, keyed by the form field. */
export type PolicyFormErrors = Partial<Record<PolicyFormField, string>>;

/** The policy fields the form edits; the capture flags it does not show stay as they were stored. */
export type TenantPolicyPayload = Omit<TenantPolicy, "prompt_capture_enabled" | "response_capture_enabled">;

const INVALID_NUMBER = "Número inválido.";
const NEGATIVE_AMOUNT = "No puede ser negativo.";
const RATE_LIMIT_RANGE = "El límite tiene que ser un entero entre 1 y 100000 pedidos por minuto.";
const SIMILARITY_RANGE = "El umbral de similitud tiene que estar entre 0 y 1.";
const MAX_AGE_RANGE = "La antigüedad máxima tiene que ser un entero entre 1 y 720 horas.";
const TARGET_RANGE = `El objetivo de calidad tiene que estar entre ${formatTarget(TARGET_MIN)} y ${formatTarget(TARGET_MAX)}.`;
const MODELS_REQUIRED = "Elegir al menos un modelo premium.";

// Digits with one optional decimal separator, point or comma, and an optional minus.
const NUMBER_TEXT = /^-?(?:\d+(?:[.,]\d+)?|[.,]\d+)$/;

/**
 * Reads a number the way the operator types it: surrounding spaces are ignored and the decimal
 * separator is a point or a comma ("10,5" is 10.5). Empty text is no value (`null`); anything
 * else that is not a plain number is "invalid", so a typo is never read as "no limit".
 */
export function parsePolicyNumber(text: string): number | null | "invalid" {
  const trimmed = text.trim();
  if (trimmed === "") {
    return null;
  }
  if (!NUMBER_TEXT.test(trimmed)) {
    return "invalid";
  }
  const value = Number(trimmed.replace(",", "."));
  if (!Number.isFinite(value)) {
    return "invalid";
  }
  // "-0" is just 0.
  return value === 0 ? 0 : value;
}

/** A stored number as field text. `String(1e-7)` is "1e-7", which the parser rejects. */
export function numberText(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "";
  }
  const text = String(value);
  return /e/i.test(text) ? value.toFixed(20).replace(/\.?0+$/, "") : text;
}

type NumberRule = {
  min?: number;
  max?: number;
  integer?: boolean;
  /** What a value out of the rule says; also what an empty required field says. */
  message: string;
};

/**
 * The one validation behind Guardar and Simular: either every field is valid and `payload` is the
 * policy to send, or `errors` names each invalid field and `payload` is null.
 */
export function validatePolicyForm(state: PolicyFormState): {
  errors: PolicyFormErrors;
  payload: TenantPolicyPayload | null;
} {
  const errors: PolicyFormErrors = {};

  // Empty is "no limit"; a typo or a value out of the rule is an error.
  function optional(field: PolicyFormField, text: string, rule: NumberRule): number | null {
    const value = parsePolicyNumber(text);
    if (value === "invalid") {
      errors[field] = INVALID_NUMBER;
      return null;
    }
    if (value === null) {
      return null;
    }
    const outOfRange =
      (rule.min !== undefined && value < rule.min) ||
      (rule.max !== undefined && value > rule.max) ||
      (rule.integer === true && !Number.isInteger(value));
    if (outOfRange) {
      errors[field] = rule.message;
      return null;
    }
    return value;
  }

  // Empty is not "no limit" here: it is as wrong as a value out of the rule.
  function required(field: PolicyFormField, text: string, rule: NumberRule): number {
    const value = optional(field, text, rule);
    if (value === null && errors[field] === undefined) {
      errors[field] = rule.message;
    }
    return value ?? Number.NaN;
  }

  const amount: NumberRule = { min: 0, message: NEGATIVE_AMOUNT };
  const routingQualityTarget = required("routingQualityTarget", state.routingQualityTarget, {
    min: TARGET_MIN,
    max: TARGET_MAX,
    message: TARGET_RANGE,
  });
  const rateLimit = optional("rateLimitRequestsPerMinute", state.rateLimitRequestsPerMinute, {
    min: 1,
    max: 100_000,
    integer: true,
    message: RATE_LIMIT_RANGE,
  });
  const maxPremiumCost = optional("maxPremiumCostPerRequest", state.maxPremiumCostPerRequest, amount);
  const hardBudget = optional("hardBudgetLimitUsd", state.hardBudgetLimitUsd, amount);
  const softBudget = optional("softBudgetUsd", state.softBudgetUsd, amount);
  const similarityThreshold = required("semanticCacheSimilarityThreshold", state.semanticCacheSimilarityThreshold, {
    min: 0,
    max: 1,
    message: SIMILARITY_RANGE,
  });
  const maxEntryAgeHours = required("semanticCacheMaxEntryAgeHours", state.semanticCacheMaxEntryAgeHours, {
    min: 1,
    max: 720,
    integer: true,
    message: MAX_AGE_RANGE,
  });
  if (state.allowedPremiumModels.length === 0) {
    errors.allowedPremiumModels = MODELS_REQUIRED;
  }

  if (Object.keys(errors).length > 0) {
    return { errors, payload: null };
  }

  return {
    errors,
    payload: {
      routing_mode_default: state.routingModeDefault,
      calibrated_routing_enabled: state.calibratedRoutingEnabled,
      fallback_enabled: state.fallbackEnabled,
      semantic_cache_enabled: state.semanticCacheEnabled,
      semantic_cache_similarity_threshold: similarityThreshold,
      semantic_cache_max_entry_age_hours: maxEntryAgeHours,
      allowed_premium_models: state.allowedPremiumModels,
      max_premium_cost_per_request: maxPremiumCost,
      hard_budget_limit_usd: hardBudget,
      hard_budget_enforcement: hardBudget === null ? null : state.hardBudgetEnforcement,
      soft_budget_usd: softBudget,
      evidence_retention_window: state.evidenceRetentionWindow,
      metadata_minimization_level: state.metadataMinimizationLevel,
      routing_quality_target: routingQualityTarget,
      rate_limit_requests_per_minute: rateLimit,
    },
  };
}
