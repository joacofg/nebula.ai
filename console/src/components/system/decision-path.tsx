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

/** Two to four decimals (`maxDecimals`): 0.9 → "0.90", 0.8312 → "0.8312". */
export function formatProb(value: number, maxDecimals = 4) {
  const fixed = value.toFixed(maxDecimals).replace(/0+$/, "");
  const [whole, decimals = ""] = fixed.split(".");
  return `${whole}.${decimals.padEnd(2, "0")}`;
}

function clears(step: DecisionStep) {
  return step.p !== null && step.tau !== null && step.p >= step.tau;
}

/** p and τ written to the same number of decimals, at least as many as it takes to tell them apart (six at most). */
function formatPair(p: number, tau: number): [string, string] {
  let decimals = 4;
  while (decimals < 6 && p !== tau && formatProb(p, decimals) === formatProb(tau, decimals)) {
    decimals += 1;
  }
  return [formatProb(p, decimals), formatProb(tau, decimals)];
}

/**
 * What a step compared, as the figure and its text alternative both write it: "p 0.82 ≥ τ 0.75".
 * Two values that round to the same text are shown with more decimals, so a "<" never sits between
 * two equal-looking numbers.
 */
function comparison(step: DecisionStep) {
  if (step.p === null) {
    return `p sin dato · τ ${step.tau === null ? "∞" : formatProb(step.tau)}`;
  }
  if (step.tau === null) {
    return `p ${formatProb(step.p)} < τ ∞`;
  }
  const [p, tau] = formatPair(step.p, step.tau);
  return `p ${p} ${clears(step) ? "≥" : "<"} τ ${tau}`;
}

function describe(steps: DecisionStep[], chosen: DecisionTier, exitRow: number) {
  const evaluated = steps.filter((_, i) => i <= exitRow);
  const parts = evaluated.map((step) => {
    if (step.p === null) {
      return `${step.tier} sin dato (${comparison(step)})`;
    }
    return clears(step) ? `${step.tier} elegido (${comparison(step)})` : `${step.tier} descartado (${comparison(step)})`;
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

/** Wide: scaled to fill a column. Compact: drawn 1:1 for a ~350 px panel. Each box holds one comparison line. */
const WIDE: Geometry = { boxW: 136, boxH: 34, row: 62, startX: 8, boxX0: 56, stepX: 150, endX: 430, width: 500 };
const COMPACT: Geometry = { boxW: 124, boxH: 34, row: 56, startX: 6, boxX0: 22, stepX: 96, endX: 260, width: 344 };
const TIERS = ["local", "economy", "frontier"] as const;

/**
 * The router cascade drawn as a signal path: every tier is on the sheet, each evaluated step
 * writes what it compared (p against τ), and only the branch that won is inked. The branches not
 * taken are dashed and their text stays at full AA contrast; nothing is faded.
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

  // The branch taken is one inked path (it traces itself); each branch not taken is its own dashed one.
  const ink: string[] = [`M${g.startX} ${cy(0)} H${boxX(0)}`];
  const dashed: { branch: string; d: string }[] = [];
  for (let i = 0; i < 2; i += 1) {
    const x = boxX(i);
    const into = i + 1 < 2 ? boxX(i + 1) : g.endX;
    const drop = { branch: `to-${TIERS[i + 1]}`, d: `M${x + g.boxW / 2} ${cy(i) + g.boxH / 2} V${cy(i + 1)} H${into}` };
    const across = { branch: `${TIERS[i]}-exit`, d: `M${x + g.boxW} ${cy(i)} H${g.endX}` };
    if (i < exitRow) {
      ink.push(drop.d);
      dashed.push(across);
    } else if (i === exitRow) {
      ink.push(across.d);
      dashed.push(drop);
    } else {
      dashed.push(drop, across);
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
      {dashed.map(({ branch, d }) => (
        <path key={branch} data-branch={branch} d={d} fill="none" strokeWidth={1} strokeDasharray="4 3" className="stroke-ink-3" />
      ))}
      <circle cx={g.startX} cy={cy(0)} r={4} className="fill-ink" />
      {steps.slice(0, 2).map((step, i) => {
        const x = boxX(i);
        const evaluated = i <= exitRow;
        const won = i === winnerIndex;
        return (
          <g key={step.tier} data-stage={step.tier} data-evaluated={String(evaluated)}>
            <rect
              x={x}
              y={cy(i) - g.boxH / 2}
              width={g.boxW}
              height={g.boxH}
              strokeWidth={won ? 1.5 : 1}
              strokeDasharray={evaluated ? undefined : "4 3"}
              className={cn("fill-surface", won ? "stroke-ink" : evaluated ? "stroke-line-strong" : "stroke-ink-3")}
            />
            <text
              x={x + g.boxW / 2}
              y={cy(i) + 4.5}
              textAnchor="middle"
              className={cn("font-label text-[13px]", evaluated ? "fill-ink" : "fill-ink-3")}
            >
              {evaluated ? comparison(step) : "no evaluado"}
            </text>
          </g>
        );
      })}
      <path data-branch="taken" d={ink.join(" ")} pathLength={1} fill="none" strokeWidth={1.5} className={cn("stroke-ink", trace ? "decision-trace" : undefined)} />
      {TIERS.map((tier, row) => {
        const isChosen = row === chosenRow || (chosenRow === -1 && row === exitRow);
        const reached = row === exitRow;
        return (
          <g
            key={tier}
            data-stage={tier === "frontier" ? "frontier" : undefined}
            data-evaluated={tier === "frontier" ? String(reached) : undefined}
            data-chosen={isChosen ? "true" : undefined}
          >
            <rect
              x={g.endX}
              y={cy(row) - 7}
              width={14}
              height={14}
              strokeWidth={1}
              className={isChosen ? (SWATCH[chosen] ?? "fill-ink") : "fill-surface stroke-ink-3"}
            />
            <text x={g.endX + 22} y={cy(row) + 4.5} className={cn("font-label text-[14px]", isChosen ? "fill-ink font-semibold" : "fill-ink-3")}>
              {isChosen ? tierLabel(chosen) : tier}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
