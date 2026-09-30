import type { Tier } from "@/lib/router-replay";

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});

/** USD per prompt → "$1.696" per 1000 prompts, the unit of the phase-3 report. */
export function formatPer1000(costPerPrompt: number) {
  return usd.format(Number.isFinite(costPerPrompt) ? costPerPrompt * 1000 : 0);
}

export function formatQuality(quality: number) {
  return Number.isFinite(quality) ? quality.toFixed(3) : "—";
}

export function formatShare(share: number) {
  return `${Math.round(share * 100)} %`;
}

/** A saving as a signed change in cost: 0.31 → "−31 %", −0.05 → "+5 %". */
export function formatSaving(saving: number | null) {
  if (saving === null || !Number.isFinite(saving)) {
    return "—";
  }
  const pct = Math.round(saving * 100);
  if (pct === 0) {
    return "0 %";
  }
  return pct > 0 ? `−${pct} %` : `+${-pct} %`;
}

export function formatCi(ci: [number, number]) {
  return `IC 95 % [${Math.round(ci[0] * 100)} %, ${Math.round(ci[1] * 100)} %]`;
}

export function formatTau(tau: number | null | undefined) {
  if (tau === null || tau === undefined || !Number.isFinite(tau)) {
    return "∞";
  }
  return tau.toFixed(2);
}

// Categorical slots 1–3 of the dataviz reference palette, validated all-pairs
// on the light surface (CVD ΔE ≥ 9.2); tier text stays in slate ink.
export const TIER_COLORS: Record<Tier, string> = {
  local: "#2a78d6",
  economy: "#eb6834",
  frontier: "#1baf7a",
};

export const TIER_LABELS: Record<Tier, string> = {
  local: "local",
  economy: "economy",
  frontier: "frontier",
};
