"use client";

import { useEffect, useState } from "react";

import { cn } from "cn";

import { tierLabel } from "@/components/system/tier-badge";

export type DecisionStep = { tier: "local" | "economy"; p: number | null; tau: number | null };
export type DecisionTier = "local" | "economy" | "frontier" | "cache" | "denied";

type DecisionPathProps = {
  steps: DecisionStep[];
  chosen: DecisionTier;
  /** Trace the path on mount (skipped under prefers-reduced-motion). */
  animate?: boolean;
  className?: string;
};

const SWATCH: Record<string, string> = {
  local: "fill-tier-local",
  economy: "fill-tier-economy",
  frontier: "fill-tier-frontier",
  cache: "fill-tier-cache",
  denied: "fill-danger",
};

/** Two to four decimals: 0.9 → "0.90", 0.8312 → "0.8312". */
function fmt(value: number) {
  const fixed = value.toFixed(4).replace(/0+$/, "");
  const [whole, decimals = ""] = fixed.split(".");
  return `${whole}.${decimals.padEnd(2, "0")}`;
}

function clears(step: DecisionStep) {
  return step.p !== null && step.tau !== null && step.p >= step.tau;
}

function describe(steps: DecisionStep[], chosen: DecisionTier, exitRow: number) {
  const evaluated = steps.filter((_, i) => i <= exitRow);
  const parts = evaluated.map((step) => {
    if (step.p === null) {
      return `${step.tier} sin dato`;
    }
    const tau = step.tau === null ? "∞" : fmt(step.tau);
    return clears(step)
      ? `${step.tier} elegido (${fmt(step.p)} ≥ ${tau})`
      : `${step.tier} descartado (${fmt(step.p)} < ${tau})`;
  });
  if (!evaluated.some((s) => s.tier === chosen && clears(s))) {
    parts.push(`${tierLabel(chosen)} elegido`);
  }
  return `Decisión: ${parts.join(", ")}`;
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(() =>
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
      : false,
  );
  useEffect(() => {
    if (typeof window.matchMedia !== "function") {
      return;
    }
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(query.matches);
    query.addEventListener?.("change", onChange);
    return () => query.removeEventListener?.("change", onChange);
  }, []);
  return reduced;
}

const BOX_W = 124;
const BOX_H = 34;
const ROW = 62;
const START_X = 8;
const BOX_X0 = 56;
const STEP_X = 150;
const END_X = 430;
const WIDTH = 500;
const TIERS = ["local", "economy", "frontier"] as const;

/**
 * The router cascade drawn as a signal path: every tier is on the sheet, the evaluated
 * steps show their probability and threshold, and only the branch that won is inked.
 */
export function DecisionPath({ steps, chosen, animate = false, className }: DecisionPathProps) {
  const reduced = usePrefersReducedMotion();
  const trace = animate && !reduced;
  const winnerIndex = steps.findIndex((s) => s.tier === chosen && clears(s));
  // The row where the path leaves toward its terminal: the winning step, or frontier.
  const exitRow = winnerIndex >= 0 ? winnerIndex : Math.max(steps.length, 2);
  const height = 24 + 3 * ROW;
  const cy = (row: number) => 36 + row * ROW;
  const boxX = (i: number) => BOX_X0 + i * STEP_X;
  const chosenRow = TIERS.indexOf(chosen as (typeof TIERS)[number]);

  const ink: string[] = [`M${START_X} ${cy(0)} H${boxX(0)}`];
  const faint: string[] = [];
  for (let i = 0; i < 2; i += 1) {
    const x = boxX(i);
    const into = i + 1 < 2 ? boxX(i + 1) : END_X;
    const drop = `M${x + BOX_W / 2} ${cy(i) + BOX_H / 2} V${cy(i + 1)} H${into}`;
    const across = `M${x + BOX_W} ${cy(i)} H${END_X}`;
    if (i < exitRow) {
      ink.push(drop);
      faint.push(across);
    } else if (i === exitRow) {
      ink.push(across);
      faint.push(drop);
    } else {
      faint.push(drop, across);
    }
  }
  return (
    <svg
      role="img"
      aria-label={describe(steps, chosen, exitRow)}
      viewBox={`0 0 ${WIDTH} ${height}`}
      className={cn("block h-auto w-full max-w-[600px] overflow-visible", className)}
    >
      <path d={faint.join(" ")} fill="none" strokeWidth={1} className="stroke-line" />
      <circle cx={START_X} cy={cy(0)} r={4} className="fill-ink" />
      {steps.slice(0, 2).map((step, i) => {
        const x = boxX(i);
        const evaluated = i <= exitRow;
        const won = i === winnerIndex;
        const tau = step.tau === null ? "∞" : fmt(step.tau);
        return (
          <g key={step.tier} data-stage={step.tier} data-evaluated={String(evaluated)} className={evaluated ? "" : "opacity-40"}>
            <rect
              x={x}
              y={cy(i) - BOX_H / 2}
              width={BOX_W}
              height={BOX_H}
              className={cn("fill-surface", won ? "stroke-ink" : "stroke-line-strong")}
              strokeWidth={won ? 1.5 : 1}
            />
            <text x={x + BOX_W / 2} y={cy(i) + 4.5} textAnchor="middle" className="fill-ink font-label text-[13px]">
              {step.p === null ? `p ${step.tier} sin dato` : `p ${step.tier} ${fmt(step.p)}`}
            </text>
            <text x={x + BOX_W + 8} y={cy(i) - 7} className="fill-ink-3 font-mono text-[11px]">
              {`τ ${tau}`}
            </text>
          </g>
        );
      })}
      <path d={ink.join(" ")} pathLength={1} fill="none" strokeWidth={1.5} className={cn("stroke-ink", trace ? "decision-trace" : undefined)} />
      {TIERS.map((tier, row) => {
        const isChosen = row === chosenRow || (chosenRow === -1 && row === exitRow);
        const reached = row === exitRow;
        return (
          <g
            key={tier}
            data-stage={tier === "frontier" ? "frontier" : undefined}
            data-evaluated={tier === "frontier" ? String(reached) : undefined}
            data-chosen={isChosen ? "true" : undefined}
            className={isChosen ? "" : "opacity-40"}
          >
            <rect x={END_X} y={cy(row) - 7} width={14} height={14} className={isChosen ? (SWATCH[chosen] ?? "fill-ink") : (SWATCH[tier] ?? "fill-line")} />
            <text x={END_X + 22} y={cy(row) + 4.5} className={cn("fill-ink font-label text-[14px]", isChosen ? "font-semibold" : "")}>
              {isChosen ? tierLabel(chosen) : tier}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
