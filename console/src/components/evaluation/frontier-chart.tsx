"use client";

import { useMemo, useRef, useState, type PointerEvent } from "react";

import { TIER_COLORS, formatPer1000, formatQuality, formatTau } from "@/components/evaluation/format";
import type { CostQuality, ReplayBaselines, ReplayOperatingPoint } from "@/lib/router-replay";

// Chart ink: the console accent for the router, slate for the random baseline
// and the non-tier references. Validated with the dataviz script (accent vs
// the tier orange: CVD ΔE 20.4, contrast ≥ 3:1 on white).
const ROUTER_COLOR = "#0369a1";
const RANDOM_COLOR = "#94a3b8";
const GRID_COLOR = "#e2e8f0";
const AXIS_COLOR = "#cbd5e1";
const REFERENCE_COLOR = "#475569";

const WIDTH = 640;
const HEIGHT = 340;
const MARGIN = { top: 20, right: 28, bottom: 52, left: 60 };
const PLOT_W = WIDTH - MARGIN.left - MARGIN.right;
const PLOT_H = HEIGHT - MARGIN.top - MARGIN.bottom;

type FrontierChartProps = {
  front: readonly ReplayOperatingPoint[];
  random: readonly CostQuality[];
  baselines: ReplayBaselines;
  current: CostQuality;
};

type Marker = {
  id: string;
  label: string;
  cost: number;
  quality: number;
  color: string;
  shape: "circle" | "diamond" | "ring";
  labelDx: number;
  labelDy: number;
  anchor: "start" | "end";
};

type Hover = { x: number; y: number; title: string; lines: string[] };

function finite(value: number, fallback = 0) {
  return Number.isFinite(value) ? value : fallback;
}

function niceStep(raw: number) {
  const exp = Math.floor(Math.log10(raw));
  const base = raw / 10 ** exp;
  const nice = base <= 1 ? 1 : base <= 2 ? 2 : base <= 2.5 ? 2.5 : base <= 5 ? 5 : 10;
  return nice * 10 ** exp;
}

/** x in USD / 1000 prompts; always a finite, non-empty domain starting at 0. */
export function costScale(maxPer1000: number) {
  const max = maxPer1000 > 0 && Number.isFinite(maxPer1000) ? maxPer1000 : 1;
  const step = niceStep(max / 4);
  const top = Math.ceil(max / step - 1e-9) * step;
  const ticks: number[] = [];
  for (let t = 0; t <= top + step / 2; t += step) {
    ticks.push(Number(t.toFixed(6)));
  }
  return { min: 0, max: top, ticks };
}

/** y in quality; 0.05 grid, at least one step tall, capped to [0, 1]. */
export function qualityScale(minQuality: number) {
  const low = Number.isFinite(minQuality) ? Math.max(0, Math.min(minQuality, 1)) : 0;
  let min = Math.floor((low - 0.01) * 20) / 20;
  min = Math.max(0, Math.min(min, 0.95));
  const ticks: number[] = [];
  for (let t = min; t <= 1 + 1e-9; t += 0.05) {
    ticks.push(Number(t.toFixed(2)));
  }
  return { min, max: 1, ticks };
}

function MarkerShape({ marker, x, y }: { marker: Marker; x: number; y: number }) {
  if (marker.shape === "diamond") {
    const s = 6;
    return (
      <polygon
        points={`${x},${y - s} ${x + s},${y} ${x},${y + s} ${x - s},${y}`}
        fill={marker.color}
        stroke="#ffffff"
        strokeWidth={2}
      />
    );
  }
  if (marker.shape === "ring") {
    return <circle cx={x} cy={y} r={5} fill="#ffffff" stroke={marker.color} strokeWidth={2.5} />;
  }
  return <circle cx={x} cy={y} r={5} fill={marker.color} stroke="#ffffff" strokeWidth={2} />;
}

export function FrontierChart({ front, random, baselines, current }: FrontierChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<Hover | null>(null);
  const [showTable, setShowTable] = useState(false);

  const markers: Marker[] = useMemo(
    () => [
      { id: "all_local", label: "Todo local", ...baselines.all_local, color: TIER_COLORS.local, shape: "circle", labelDx: 10, labelDy: 16, anchor: "start" },
      { id: "all_economy", label: "Todo economy", ...baselines.all_economy, color: TIER_COLORS.economy, shape: "circle", labelDx: 10, labelDy: 16, anchor: "start" },
      { id: "all_frontier", label: "Todo frontier", ...baselines.all_frontier, color: TIER_COLORS.frontier, shape: "circle", labelDx: -8, labelDy: -9, anchor: "end" },
      { id: "heuristic", label: "Heurística", ...baselines.heuristic_premium_frontier, color: REFERENCE_COLOR, shape: "diamond", labelDx: 10, labelDy: -8, anchor: "start" },
      { id: "oracle", label: "Oráculo", ...baselines.oracle, color: REFERENCE_COLOR, shape: "ring", labelDx: 10, labelDy: -6, anchor: "start" },
    ],
    [baselines],
  );

  const { xs, ys } = useMemo(() => {
    const costs = [
      ...front.map((p) => p.cost_per_prompt),
      ...random.map((p) => p.cost),
      ...markers.map((m) => m.cost),
      current.cost,
    ].map((c) => finite(c) * 1000);
    const qualities = [
      ...front.map((p) => p.quality),
      ...random.map((p) => p.quality),
      ...markers.map((m) => m.quality),
      current.quality,
    ].map((q) => finite(q, 1));
    return { xs: costScale(Math.max(0, ...costs)), ys: qualityScale(Math.min(1, ...qualities)) };
  }, [front, random, markers, current]);

  const x = (costPerPrompt: number) =>
    MARGIN.left + ((finite(costPerPrompt) * 1000 - xs.min) / (xs.max - xs.min)) * PLOT_W;
  const y = (quality: number) =>
    MARGIN.top + (1 - (finite(quality, 1) - ys.min) / (ys.max - ys.min)) * PLOT_H;

  const routerPath = front.map((p) => `${x(p.cost_per_prompt).toFixed(1)},${y(p.quality).toFixed(1)}`).join(" ");
  const randomPath = random.map((p) => `${x(p.cost).toFixed(1)},${y(p.quality).toFixed(1)}`).join(" ");

  function showPoint(px: number, py: number, title: string, lines: string[]) {
    setHover({ x: px, y: py, title, lines });
  }

  function onPlotMove(event: PointerEvent<SVGRectElement>) {
    const svg = svgRef.current;
    if (!svg || front.length === 0) {
      return;
    }
    const box = svg.getBoundingClientRect();
    if (box.width === 0) {
      return;
    }
    const vx = ((event.clientX - box.left) / box.width) * WIDTH;
    let nearest = front[0];
    for (const p of front) {
      if (Math.abs(x(p.cost_per_prompt) - vx) < Math.abs(x(nearest.cost_per_prompt) - vx)) {
        nearest = p;
      }
    }
    showPoint(x(nearest.cost_per_prompt), y(nearest.quality), "Router v1", [
      `${formatPer1000(nearest.cost_per_prompt)} / 1000 · calidad ${formatQuality(nearest.quality)}`,
      `τ_local ${formatTau(nearest.tau_local)} · τ_economy ${formatTau(nearest.tau_economy)}`,
    ]);
  }

  return (
    <figure className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-600" aria-hidden>
        <span className="inline-flex items-center gap-2">
          <span className="inline-block h-0.5 w-5 rounded" style={{ backgroundColor: ROUTER_COLOR }} />
          Router v1 (puntos de operación)
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="inline-block h-0.5 w-5 rounded" style={{ backgroundColor: RANDOM_COLOR }} />
          Mezcla aleatoria más barata
        </span>
        <span className="inline-flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 rounded-full border-2"
            style={{ borderColor: ROUTER_COLOR, backgroundColor: "#ffffff" }}
          />
          Punto actual
        </span>
      </div>

      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="h-auto w-full"
          role="img"
          aria-label={`Frontera costo/calidad del router: punto actual ${formatPer1000(current.cost)} por 1000 prompts, calidad ${formatQuality(current.quality)}`}
          onPointerLeave={() => setHover(null)}
        >
          {ys.ticks.map((t) => (
            <g key={`y-${t}`}>
              <line x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(t)} y2={y(t)} stroke={GRID_COLOR} strokeWidth={1} />
              <text x={MARGIN.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-slate-500 text-[11px] tabular-nums">
                {t.toFixed(2)}
              </text>
            </g>
          ))}
          {xs.ticks.map((t) => {
            const px = MARGIN.left + ((t - xs.min) / (xs.max - xs.min)) * PLOT_W;
            return (
              <g key={`x-${t}`}>
                <line x1={px} x2={px} y1={HEIGHT - MARGIN.bottom} y2={HEIGHT - MARGIN.bottom + 4} stroke={AXIS_COLOR} strokeWidth={1} />
                <text x={px} y={HEIGHT - MARGIN.bottom + 18} textAnchor="middle" className="fill-slate-500 text-[11px] tabular-nums">
                  {t.toFixed(t < 1 && t > 0 ? 2 : 1)}
                </text>
              </g>
            );
          })}
          <line
            x1={MARGIN.left}
            x2={WIDTH - MARGIN.right}
            y1={HEIGHT - MARGIN.bottom}
            y2={HEIGHT - MARGIN.bottom}
            stroke={AXIS_COLOR}
            strokeWidth={1}
          />
          <text x={MARGIN.left + PLOT_W / 2} y={HEIGHT - 10} textAnchor="middle" className="fill-slate-600 text-[12px]">
            Costo (USD / 1000 prompts)
          </text>
          <text
            transform={`translate(16 ${MARGIN.top + PLOT_H / 2}) rotate(-90)`}
            textAnchor="middle"
            className="fill-slate-600 text-[12px]"
          >
            Calidad
          </text>

          {random.length > 1 ? (
            <polyline
              data-testid="random-mix"
              points={randomPath}
              fill="none"
              stroke={RANDOM_COLOR}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ) : random.length === 1 ? (
            <circle data-testid="random-mix" cx={x(random[0].cost)} cy={y(random[0].quality)} r={4} fill={RANDOM_COLOR} />
          ) : null}

          {front.length > 1 ? (
            <polyline
              data-testid="router-curve"
              points={routerPath}
              fill="none"
              stroke={ROUTER_COLOR}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ) : front.length === 1 ? (
            <circle
              data-testid="router-curve"
              cx={x(front[0].cost_per_prompt)}
              cy={y(front[0].quality)}
              r={4}
              fill={ROUTER_COLOR}
            />
          ) : null}

          <rect
            x={MARGIN.left}
            y={MARGIN.top}
            width={PLOT_W}
            height={PLOT_H}
            fill="transparent"
            onPointerMove={onPlotMove}
          />

          {markers.map((m) => {
            const mx = x(m.cost);
            const my = y(m.quality);
            const lines = [`${formatPer1000(m.cost)} / 1000 · calidad ${formatQuality(m.quality)}`];
            return (
              <g
                key={m.id}
                tabIndex={0}
                role="img"
                aria-label={`${m.label}: ${lines[0]}`}
                className="outline-none focus-visible:[&>circle:first-child]:stroke-slate-400"
                onPointerEnter={() => showPoint(mx, my, m.label, lines)}
                onFocus={() => showPoint(mx, my, m.label, lines)}
                onBlur={() => setHover(null)}
              >
                <circle cx={mx} cy={my} r={12} fill="transparent" />
                <MarkerShape marker={m} x={mx} y={my} />
                <text
                  x={mx + m.labelDx}
                  y={my + m.labelDy}
                  textAnchor={m.anchor}
                  className="pointer-events-none fill-slate-700 text-[11px] font-medium"
                >
                  {m.label}
                </text>
              </g>
            );
          })}

          <g data-testid="current-point" pointerEvents="none">
            <circle cx={x(current.cost)} cy={y(current.quality)} r={9} fill={ROUTER_COLOR} fillOpacity={0.15} />
            <circle cx={x(current.cost)} cy={y(current.quality)} r={6} fill="#ffffff" stroke={ROUTER_COLOR} strokeWidth={3} />
          </g>
        </svg>

        {hover ? (
          <div
            role="tooltip"
            className="pointer-events-none absolute z-10 min-w-44 -translate-x-1/2 -translate-y-full rounded-lg border border-border bg-white px-3 py-2 text-xs shadow-panel"
            style={{ left: `${(hover.x / WIDTH) * 100}%`, top: `calc(${(hover.y / HEIGHT) * 100}% - 12px)` }}
          >
            <div className="font-semibold text-slate-950">{hover.lines[0]}</div>
            {hover.lines.slice(1).map((line) => (
              <div key={line} className="text-slate-600">
                {line}
              </div>
            ))}
            <div className="mt-1 text-slate-500">{hover.title}</div>
          </div>
        ) : null}
      </div>

      <figcaption className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
        <span>
          Cada vértice de la curva azul es un par de umbrales (τ_local, τ_economy): probabilidades fuera de fold,
          umbrales elegidos sobre el mismo corpus (la cifra fuera de muestra es la anidada). Más arriba y a la izquierda
          es mejor.
        </span>
        <button type="button" className="font-semibold text-sky-700 hover:underline" onClick={() => setShowTable((v) => !v)}>
          {showTable ? "Ocultar tabla" : "Ver tabla"}
        </button>
      </figcaption>

      {showTable ? (
        <div className="max-h-72 overflow-auto rounded-xl border border-border">
          <table aria-label="Valores del gráfico" className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-slate-50 text-slate-600">
              <tr>
                <th className="px-3 py-2 font-semibold">Política</th>
                <th className="px-3 py-2 text-right font-semibold">USD / 1000</th>
                <th className="px-3 py-2 text-right font-semibold">Calidad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono tabular-nums text-slate-800">
              {markers.map((m) => (
                <tr key={m.id}>
                  <td className="px-3 py-1.5 font-sans">{m.label}</td>
                  <td className="px-3 py-1.5 text-right">{(finite(m.cost) * 1000).toFixed(3)}</td>
                  <td className="px-3 py-1.5 text-right">{formatQuality(m.quality)}</td>
                </tr>
              ))}
              <tr>
                <td className="px-3 py-1.5 font-sans">Heurística (economy)</td>
                <td className="px-3 py-1.5 text-right">{(finite(baselines.heuristic_premium_economy.cost) * 1000).toFixed(3)}</td>
                <td className="px-3 py-1.5 text-right">{formatQuality(baselines.heuristic_premium_economy.quality)}</td>
              </tr>
              {front.map((p) => (
                <tr key={`${p.tau_local}-${p.tau_economy}`}>
                  <td className="px-3 py-1.5 font-sans">
                    Router τ_local {formatTau(p.tau_local)} · τ_economy {formatTau(p.tau_economy)}
                  </td>
                  <td className="px-3 py-1.5 text-right">{(finite(p.cost_per_prompt) * 1000).toFixed(3)}</td>
                  <td className="px-3 py-1.5 text-right">{formatQuality(p.quality)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </figure>
  );
}
