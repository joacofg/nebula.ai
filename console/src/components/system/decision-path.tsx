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

function describe(steps: DecisionStep[], chosen: DecisionTier) {
  const parts = steps.map((step) => {
    if (step.p === null) {
      return `${step.tier} sin dato`;
    }
    const tau = step.tau === null ? "∞" : fmt(step.tau);
    return clears(step)
      ? `${step.tier} elegido (${fmt(step.p)} ≥ ${tau})`
      : `${step.tier} descartado (${fmt(step.p)} < ${tau})`;
  });
  const last = steps[steps.length - 1];
  if (!last || !clears(last) || last.tier !== chosen) {
    if (!steps.some((s) => s.tier === chosen && clears(s))) {
      parts.push(`${tierLabel(chosen)} elegido`);
    }
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

const BOX_W = 112;
const BOX_H = 32;
const ROW = 64;
const START_X = 8;
const BOX_X0 = 64;
const STEP_X = 136;
const END_X = 356;

/**
 * The router cascade drawn as a signal path: each evaluated step is a box with its
 * probability and threshold; the branch that won is inked, the rest stay as hairlines.
 */
export function DecisionPath({ steps, chosen, animate = false, className }: DecisionPathProps) {
  const reduced = usePrefersReducedMotion();
  const trace = animate && !reduced;
  const winnerIndex = steps.findIndex((s) => s.tier === chosen && clears(s));
  // The row where the path leaves toward the final node.
  const exitRow = winnerIndex >= 0 ? winnerIndex : steps.length;
  const height = 24 + (exitRow + 1) * ROW + 8;
  const traceClass = trace ? "decision-trace" : undefined;

  const ink: string[] = [];
  const cy = (row: number) => 40 + row * ROW;
  const boxX = (i: number) => BOX_X0 + i * STEP_X;

  ink.push(`M${START_X} ${cy(0)} H${boxX(0)}`);
  steps.forEach((step, i) => {
    if (i > exitRow) {
      return;
    }
    const x = boxX(i);
    if (i === exitRow) {
      ink.push(`M${x + BOX_W} ${cy(i)} H${END_X}`);
      return;
    }
    // Rejected: drop from the box to the next row and run into the next box (or the end).
    const nextX = i + 1 < steps.length ? boxX(i + 1) : END_X;
    ink.push(`M${x + BOX_W / 2} ${cy(i) + BOX_H / 2} V${cy(i + 1)} H${nextX}`);
  });

  return (
    <svg
      role="img"
      aria-label={describe(steps, chosen)}
      viewBox={`0 0 400 ${height}`}
      className={cn("block h-auto w-full max-w-[400px] overflow-visible", className)}
    >
      <circle cx={START_X} cy={cy(0)} r={4} className="fill-ink" />
      {steps.map((step, i) => {
        const x = boxX(i);
        const evaluated = i <= exitRow;
        const won = i === winnerIndex;
        const tau = step.tau === null ? "∞" : fmt(step.tau);
        return (
          <g key={step.tier} className={evaluated ? "" : "opacity-40"}>
            <rect
              x={x}
              y={cy(i) - BOX_H / 2}
              width={BOX_W}
              height={BOX_H}
              className={cn("fill-surface", won ? "stroke-ink" : "stroke-line-strong")}
              strokeWidth={1.5}
            />
            <text x={x + BOX_W / 2} y={cy(i) + 4} textAnchor="middle" className="fill-ink font-label text-[12px]">
              {step.p === null ? `p ${step.tier} sin dato` : `p ${step.tier} ${fmt(step.p)}`}
            </text>
            <text x={x + BOX_W + 6} y={cy(i) - 8} className="fill-ink-3 font-mono text-[11px]">
              {clears(step) ? `≥ ${tau}` : `< ${tau}`}
            </text>
            {!won && evaluated ? (
              <>
                <path d={`M${x + BOX_W} ${cy(i)} H${x + BOX_W + 40}`} className="stroke-line" strokeWidth={1.5} fill="none" />
                <text x={x + BOX_W + 46} y={cy(i) + 4} className="fill-ink-3 font-label text-[12px]">
                  {`${step.tier} ✕`}
                </text>
              </>
            ) : null}
          </g>
        );
      })}
      <path
        d={ink.join(" ")}
        pathLength={1}
        fill="none"
        strokeWidth={1.5}
        className={cn("stroke-ink", traceClass)}
      />
      <g data-chosen="true">
        <rect x={END_X} y={cy(exitRow) - 7} width={14} height={14} className={SWATCH[chosen] ?? "fill-ink"} />
        <text x={END_X + 7} y={cy(exitRow) + 24} textAnchor="middle" className="fill-ink font-label text-[13px] font-semibold">
          {tierLabel(chosen)}
        </text>
      </g>
    </svg>
  );
}
