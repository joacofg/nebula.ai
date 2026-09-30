"use client";

import { useMemo, useRef, useState, type PointerEvent } from "react";

import { TIER_COLORS, formatPer1000, formatQuality, formatTau, formatUsd1000 } from "@/components/evaluation/format";
import type { CostQuality, ReplayBaselines, ReplayOperatingPoint } from "@/lib/router-replay";

// Plano chart ink: the router is drawn in ink, the random mix dashed, the
// operator's chosen point in the selection red; tiers use the ordinal ramp.
const ROUTER_COLOR = "var(--color-ink)";
const RANDOM_COLOR = "var(--color-ink-3)";
const GRID_COLOR = "var(--color-line)";
const MINOR_COLOR = "var(--color-line)";
const FRAME_COLOR = "var(--color-ink)";
const REFERENCE_COLOR = "var(--color-ink-3)";
const CHOSEN_COLOR = "var(--color-mark)";

const WIDTH = 720;
const HEIGHT = 400;
const MARGIN = { top: 28, right: 20, bottom: 48, left: 52 };
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
  shape: "circle" | "diamond" | "ring-3";
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
        stroke="var(--color-surface)"
        strokeWidth={2}
      />
    );
  }
  if (marker.shape === "ring-3") {
    return <circle cx={x} cy={y} r={5} fill="var(--color-surface)" stroke={marker.color} strokeWidth={2.5} />;
  }
  return <circle cx={x} cy={y} r={5} fill={marker.color} stroke="var(--color-surface)" strokeWidth={2} />;
}

export function FrontierChart({ front, random, baselines, current }: FrontierChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<Hover | null>(null);
  const [showTable, setShowTable] = useState(false);

  const markers: Marker[] = useMemo(
    () => [
      { id: "all_local", label: "todo local", ...baselines.all_local, color: TIER_COLORS.local, shape: "circle", labelDx: 10, labelDy: 16, anchor: "start" },
      { id: "all_economy", label: "todo economy", ...baselines.all_economy, color: TIER_COLORS.economy, shape: "circle", labelDx: 10, labelDy: 16, anchor: "start" },
      { id: "all_frontier", label: "todo frontier", ...baselines.all_frontier, color: TIER_COLORS.frontier, shape: "circle", labelDx: -8, labelDy: -9, anchor: "end" },
      { id: "heuristic", label: "heurística v0 (base)", ...baselines.heuristic_premium_frontier, color: REFERENCE_COLOR, shape: "diamond", labelDx: 10, labelDy: -8, anchor: "start" },
      { id: "oracle", label: "oráculo", ...baselines.oracle, color: REFERENCE_COLOR, shape: "ring-3", labelDx: 10, labelDy: -6, anchor: "start" },
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
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 font-label text-[13px] font-medium text-ink-2" aria-hidden>
        <span className="inline-flex items-center gap-2">
          <span className="inline-block w-5 border-t-2" style={{ borderColor: ROUTER_COLOR }} />
          router v1
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="inline-block w-5 border-t-[1.5px] border-dashed" style={{ borderColor: RANDOM_COLOR }} />
          mezcla aleatoria más barata
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: CHOSEN_COLOR }} />
          punto elegido
        </span>
      </div>

      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="h-auto w-full"
          role="group"
          aria-label={`Frontera costo–calidad del router: punto elegido ${formatUsd1000(current.cost)} por 1000 pedidos, calidad ${formatQuality(current.quality)}`}
          onPointerLeave={() => setHover(null)}
        >
          {/* Oscilloscope graticule: major lines at the ticks, minor marks on the centre axes. */}
          {xs.ticks.slice(0, -1).flatMap((t, i) => {
            const x0 = MARGIN.left + ((t - xs.min) / (xs.max - xs.min)) * PLOT_W;
            const step = PLOT_W / (xs.ticks.length - 1) / 5;
            return [1, 2, 3, 4].map((k) => (
              <line
                key={`mx-${i}-${k}`}
                x1={x0 + step * k}
                x2={x0 + step * k}
                y1={MARGIN.top + PLOT_H / 2 - 3}
                y2={MARGIN.top + PLOT_H / 2 + 3}
                stroke={MINOR_COLOR}
              />
            ));
          })}
          {ys.ticks.slice(0, -1).flatMap((t, i) => {
            const y0 = y(t);
            const step = (y(ys.ticks[i + 1]) - y0) / 5;
            return [1, 2, 3, 4].map((k) => (
              <line
                key={`my-${i}-${k}`}
                x1={MARGIN.left + PLOT_W / 2 - 3}
                x2={MARGIN.left + PLOT_W / 2 + 3}
                y1={y0 + step * k}
                y2={y0 + step * k}
                stroke={MINOR_COLOR}
              />
            ));
          })}
          {xs.ticks.map((t) => {
            const px = MARGIN.left + ((t - xs.min) / (xs.max - xs.min)) * PLOT_W;
            return (
              <line key={`gx-${t}`} x1={px} x2={px} y1={MARGIN.top} y2={MARGIN.top + PLOT_H} stroke={GRID_COLOR} strokeWidth={1} />
            );
          })}
          {ys.ticks.map((t) => (
            <g key={`y-${t}`}>
              <line x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(t)} y2={y(t)} stroke={GRID_COLOR} strokeWidth={1} />
              <text x={MARGIN.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-ink-3 font-mono text-[11px]">
                {t.toFixed(2)}
              </text>
            </g>
          ))}
          {xs.ticks.map((t) => {
            const px = MARGIN.left + ((t - xs.min) / (xs.max - xs.min)) * PLOT_W;
            return (
              <text key={`x-${t}`} x={px} y={HEIGHT - MARGIN.bottom + 18} textAnchor="middle" className="fill-ink-3 font-mono text-[11px]">
                {t.toFixed(t < 1 && t > 0 ? 2 : 1)}
              </text>
            );
          })}
          <rect x={MARGIN.left} y={MARGIN.top} width={PLOT_W} height={PLOT_H} fill="none" stroke={FRAME_COLOR} strokeWidth={1} />
          <text x={WIDTH - MARGIN.right} y={HEIGHT - 8} textAnchor="end" className="fill-ink-2 font-label text-[12px]">
            Costo · USD / 1000 pedidos
          </text>
          <text x={MARGIN.left} y={MARGIN.top - 10} className="fill-ink-2 font-label text-[12px]">
            Calidad
          </text>

          {random.length > 1 ? (
            <polyline
              data-testid="random-mix"
              points={randomPath}
              fill="none"
              stroke={RANDOM_COLOR}
              strokeWidth={1.5}
              strokeDasharray="5 4"
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
                className="outline-hidden [&>circle:first-child]:focus-visible:stroke-mark"
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
                  className="pointer-events-none fill-ink-2 font-label text-[12px] font-medium"
                >
                  {m.label}
                </text>
              </g>
            );
          })}

          {/* The chosen point slides along the curve; the crosshair measures it on both axes. */}
          <g pointerEvents="none" className="motion-safe:transition-transform motion-safe:duration-250 motion-safe:ease-out-expo" style={{ transform: `translateX(${x(current.cost)}px)` }}>
            <line x1={0} x2={0} y1={MARGIN.top} y2={MARGIN.top + PLOT_H} stroke={CHOSEN_COLOR} strokeWidth={1} strokeDasharray="2 3" />
          </g>
          <g pointerEvents="none" className="motion-safe:transition-transform motion-safe:duration-250 motion-safe:ease-out-expo" style={{ transform: `translateY(${y(current.quality)}px)` }}>
            <line x1={MARGIN.left} x2={MARGIN.left + PLOT_W} y1={0} y2={0} stroke={CHOSEN_COLOR} strokeWidth={1} strokeDasharray="2 3" />
          </g>
          <g
            data-testid="current-point"
            pointerEvents="none"
            className="motion-safe:transition-transform motion-safe:duration-250 motion-safe:ease-out-expo"
            style={{ transform: `translate(${x(current.cost)}px, ${y(current.quality)}px)` }}
          >
            <circle r={9} fill="none" stroke={CHOSEN_COLOR} strokeWidth={1.5} />
            <circle r={5} fill={CHOSEN_COLOR} />
          </g>
        </svg>

        {hover ? (
          <div
            role="tooltip"
            className="pointer-events-none absolute z-10 min-w-44 -translate-x-1/2 -translate-y-full border border-ink bg-surface px-3 py-2 text-[13px]"
            style={{ left: `${(hover.x / WIDTH) * 100}%`, top: `calc(${(hover.y / HEIGHT) * 100}% - 12px)` }}
          >
            <div className="font-semibold text-ink">{hover.lines[0]}</div>
            {hover.lines.slice(1).map((line) => (
              <div key={line} className="text-ink-3">
                {line}
              </div>
            ))}
            <div className="mt-1 text-ink-3">{hover.title}</div>
          </div>
        ) : null}
      </div>

      <div className="flex justify-end">
        <button type="button" className="text-sm font-semibold text-ink underline underline-offset-4 hover:text-mark" onClick={() => setShowTable((v) => !v)}>
          {showTable ? "Ocultar tabla" : "Ver tabla"}
        </button>
      </div>

      {showTable ? (
        <div className="max-h-72 overflow-auto border border-line">
          <table aria-label="Valores del gráfico" className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-canvas text-ink-3">
              <tr>
                <th className="px-3 py-2 font-semibold">Política</th>
                <th className="px-3 py-2 text-right font-semibold">USD / 1000</th>
                <th className="px-3 py-2 text-right font-semibold">Calidad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-mono text-ink-2">
              {markers.map((m) => (
                <tr key={m.id}>
                  <td className="px-3 py-1.5 font-sans">{m.label}</td>
                  <td className="px-3 py-1.5 text-right">{(finite(m.cost) * 1000).toFixed(3)}</td>
                  <td className="px-3 py-1.5 text-right">{formatQuality(m.quality)}</td>
                </tr>
              ))}
              <tr>
                <td className="px-3 py-1.5 font-sans">heurística v0 (economy)</td>
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
    </div>
  );
}
