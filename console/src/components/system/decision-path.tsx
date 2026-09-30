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
  /** Drawn at its own size for a narrow panel, so the labels stay legible. */
  compact?: boolean;
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

type Geometry = {
  boxW: number;
  boxH: number;
  row: number;
  startX: number;
  boxX0: number;
  stepX: number;
  endX: number;
  width: number;
};

/** Wide: scaled to fill a column. Compact: drawn 1:1 for a ~350 px panel, τ inside each box. */
const WIDE: Geometry = { boxW: 124, boxH: 34, row: 62, startX: 8, boxX0: 56, stepX: 150, endX: 430, width: 500 };
const COMPACT: Geometry = { boxW: 112, boxH: 44, row: 60, startX: 6, boxX0: 22, stepX: 96, endX: 252, width: 336 };
const TIERS = ["local", "economy", "frontier"] as const;

/**
 * The router cascade drawn as a signal path: every tier is on the sheet, the evaluated
 * steps show their probability and threshold, and only the branch that won is inked.
 */
export function DecisionPath({ steps, chosen, animate = false, compact = false, className }: DecisionPathProps) {
  const g = compact ? COMPACT : WIDE;
  const reduced = usePrefersReducedMotion();
  const trace = animate && !reduced;
  const winnerIndex = steps.findIndex((s) => s.tier === chosen && clears(s));
  // The row where the path leaves toward its terminal: the winning step, or frontier.
  const exitRow = winnerIndex >= 0 ? winnerIndex : Math.max(steps.length, 2);
  const height = 24 + 3 * g.row;
  const cy = (row: number) => 36 + row * g.row;
  const boxX = (i: number) => g.boxX0 + i * g.stepX;
  const chosenRow = TIERS.indexOf(chosen as (typeof TIERS)[number]);

  const ink: string[] = [`M${g.startX} ${cy(0)} H${boxX(0)}`];
  const faint: string[] = [];
  for (let i = 0; i < 2; i += 1) {
    const x = boxX(i);
    const into = i + 1 < 2 ? boxX(i + 1) : g.endX;
    const drop = `M${x + g.boxW / 2} ${cy(i) + g.boxH / 2} V${cy(i + 1)} H${into}`;
    const across = `M${x + g.boxW} ${cy(i)} H${g.endX}`;
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
      viewBox={`0 0 ${g.width} ${height}`}
      width={compact ? g.width : undefined}
      className={cn("block h-auto overflow-visible", compact ? "max-w-full" : "w-full max-w-[600px]", className)}
    >
      <path d={faint.join(" ")} fill="none" strokeWidth={1} className="stroke-line" />
      <circle cx={g.startX} cy={cy(0)} r={4} className="fill-ink" />
      {steps.slice(0, 2).map((step, i) => {
        const x = boxX(i);
        const evaluated = i <= exitRow;
        const won = i === winnerIndex;
        const tau = step.tau === null ? "∞" : fmt(step.tau);
        return (
          <g key={step.tier} data-stage={step.tier} data-evaluated={String(evaluated)} className={evaluated ? "" : "opacity-40"}>
            <rect
              x={x}
              y={cy(i) - g.boxH / 2}
              width={g.boxW}
              height={g.boxH}
              className={cn("fill-surface", won ? "stroke-ink" : "stroke-line-strong")}
              strokeWidth={won ? 1.5 : 1}
            />
            <text x={x + g.boxW / 2} y={compact ? cy(i) - 3 : cy(i) + 4.5} textAnchor="middle" className="fill-ink font-label text-[13px]">
              {step.p === null ? `p ${step.tier} sin dato` : `p ${step.tier} ${fmt(step.p)}`}
            </text>
            <text
              x={compact ? x + g.boxW / 2 : x + g.boxW + 8}
              y={compact ? cy(i) + 13 : cy(i) - 7}
              textAnchor={compact ? "middle" : undefined}
              className="fill-ink-3 font-label text-[12px]"
            >
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
            <rect x={g.endX} y={cy(row) - 7} width={14} height={14} className={isChosen ? (SWATCH[chosen] ?? "fill-ink") : (SWATCH[tier] ?? "fill-line")} />
            <text x={g.endX + 22} y={cy(row) + 4.5} className={cn("fill-ink font-label text-[14px]", isChosen ? "font-semibold" : "")}>
              {isChosen ? tierLabel(chosen) : tier}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
