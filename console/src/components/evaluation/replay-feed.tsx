"use client";

import { useEffect, useRef, useState } from "react";

import { Check, Pause, Play, RotateCcw, SkipForward, X } from "lucide-react";

import { TIER_COLORS, formatPer1000, formatQuality } from "@/components/evaluation/format";
import { routeRow, tierOutcome, type ReplayOperatingPoint, type ReplayRow, type Tier } from "@/lib/router-replay";

const SPEEDS = [1, 10, 100] as const;
type Speed = (typeof SPEEDS)[number];

// Ticks every 100 ms; `speed` prompts per second, counted in integer tenths so
// ten ticks at 1× are exactly one prompt.
const TICK_MS = 100;
const VISIBLE_ITEMS = 8;

type Decision = {
  index: number;
  row: ReplayRow;
  tier: Tier;
  ok: boolean;
  cost: number;
};

type ReplayFeedProps = {
  rows: readonly ReplayRow[];
  order: readonly number[];
  point: ReplayOperatingPoint;
  initialPlaying: boolean;
};

type FeedState = {
  position: number;
  decisions: Decision[];
  cost: number;
  ok: number;
};

const EMPTY: FeedState = { position: 0, decisions: [], cost: 0, ok: 0 };

function advance(
  state: FeedState,
  steps: number,
  rows: readonly ReplayRow[],
  order: readonly number[],
  point: ReplayOperatingPoint,
): FeedState {
  let { position, cost, ok } = state;
  const fresh: Decision[] = [];
  const end = Math.min(order.length, position + steps);
  for (; position < end; position += 1) {
    const row = rows[order[position]];
    const tier = routeRow(row, point);
    const outcome = tierOutcome(row, tier);
    cost += outcome.cost;
    ok += outcome.ok ? 1 : 0;
    fresh.push({ index: position, row, tier, ok: outcome.ok, cost: outcome.cost });
  }
  if (fresh.length === 0) {
    return state;
  }
  const decisions = [...fresh.reverse(), ...state.decisions].slice(0, VISIBLE_ITEMS);
  return { position, decisions, cost, ok };
}

export function ReplayFeed({ rows, order, point, initialPlaying }: ReplayFeedProps) {
  const [state, setState] = useState<FeedState>(EMPTY);
  const [playing, setPlaying] = useState(initialPlaying);
  const [speed, setSpeed] = useState<Speed>(1);
  const [started, setStarted] = useState(initialPlaying);
  // The live point, read at each tick: moving the slider re-routes from the
  // current prompt on, and decisions already made keep their tier.
  const pointRef = useRef(point);
  pointRef.current = point;

  const total = order.length;
  const finished = state.position >= total;

  useEffect(() => {
    if (!playing || finished) {
      return;
    }
    let carry = 0;
    const id = window.setInterval(() => {
      carry += speed;
      const steps = Math.floor(carry / 10);
      carry %= 10;
      if (steps > 0) {
        setState((prev) => advance(prev, steps, rows, order, pointRef.current));
      }
    }, TICK_MS);
    return () => window.clearInterval(id);
  }, [playing, finished, speed, rows, order]);

  const processed = state.position;
  const avgCost = processed > 0 ? state.cost / processed : 0;
  const quality = processed > 0 ? state.ok / processed : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        {finished ? (
          <button
            type="button"
            className="secondary-button gap-2"
            onClick={() => {
              setState(EMPTY);
              setPlaying(true);
            }}
          >
            <RotateCcw className="h-4 w-4" aria-hidden />
            Reiniciar
          </button>
        ) : playing ? (
          <button type="button" className="secondary-button gap-2" onClick={() => setPlaying(false)}>
            <Pause className="h-4 w-4" aria-hidden />
            Pausar
          </button>
        ) : (
          <button
            type="button"
            className="action-button gap-2"
            onClick={() => {
              setStarted(true);
              setPlaying(true);
            }}
          >
            <Play className="h-4 w-4" aria-hidden />
            {started || processed > 0 ? "Reanudar" : "Reproducir"}
          </button>
        )}
        <button
          type="button"
          className="secondary-button gap-2"
          disabled={finished}
          onClick={() => setState((prev) => advance(prev, 1, rows, order, pointRef.current))}
        >
          <SkipForward className="h-4 w-4" aria-hidden />
          Paso
        </button>
        <div role="group" aria-label="Velocidad" className="inline-flex rounded-xl border border-border bg-white p-1">
          {SPEEDS.map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={speed === s}
              className={`min-h-9 rounded-lg px-3 text-sm font-semibold transition focus:outline-hidden focus-visible:ring-2 focus-visible:ring-accent/30 ${
                speed === s ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
              }`}
              onClick={() => setSpeed(s)}
            >
              {s}×
            </button>
          ))}
        </div>
        <span className="font-mono text-sm tabular-nums text-slate-600">
          {processed} / {total} prompts
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div role="group" aria-label="Costo acumulado" className="rounded-xl border border-border bg-slate-50 px-4 py-3">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Costo acumulado</div>
          <div className="mt-1 text-xl font-semibold text-slate-950">{formatPer1000(avgCost)}</div>
          <div className="text-xs text-slate-500">USD / 1000 prompts, promedio de lo ruteado</div>
        </div>
        <div role="group" aria-label="Calidad acumulada" className="rounded-xl border border-border bg-slate-50 px-4 py-3">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Calidad acumulada</div>
          <div className="mt-1 text-xl font-semibold text-slate-950">{formatQuality(quality)}</div>
          <div className="text-xs text-slate-500">share de respuestas suficientes según la etiqueta</div>
        </div>
      </div>

      {state.decisions.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border px-4 py-6 text-center text-sm text-slate-500">
          El replay recorre los prompts del corpus en un orden fijo. Reproducí o avanzá un paso.
        </p>
      ) : (
        <ol className="divide-y divide-slate-100 rounded-xl border border-border" aria-label="Últimos prompts ruteados">
          {state.decisions.map((d) => (
            <li key={d.index} className="flex items-start gap-3 px-4 py-2.5 text-sm">
              <span className="mt-0.5 w-12 shrink-0 font-mono text-xs tabular-nums text-slate-400">#{d.index + 1}</span>
              <span className="inline-flex w-24 shrink-0 items-center gap-1.5 font-mono text-xs font-semibold text-slate-800">
                <span
                  aria-hidden
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: TIER_COLORS[d.tier] }}
                />
                {d.tier}
              </span>
              <span className="min-w-0 flex-1 truncate text-slate-700" title={d.row.text}>
                <span className="mr-2 font-mono text-xs uppercase text-slate-400">{d.row.lang}</span>
                {d.row.text}
              </span>
              {d.ok ? (
                <Check className="h-4 w-4 shrink-0 text-emerald-700" aria-label="suficiente" role="img" />
              ) : (
                <X className="h-4 w-4 shrink-0 text-rose-700" aria-label="insuficiente" role="img" />
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
