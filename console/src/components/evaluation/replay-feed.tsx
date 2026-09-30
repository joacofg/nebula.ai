"use client";

import { useEffect, useRef, useState } from "react";

import { Check, Pause, Play, RotateCcw, SkipForward, X } from "lucide-react";

import { formatQuality, formatUsd1000 } from "@/components/evaluation/format";
import { Readout } from "@/components/system/readout";
import { TierBadge } from "@/components/system/tier-badge";
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
        <div role="group" aria-label="Velocidad" className="inline-flex border border-line bg-surface">
          {SPEEDS.map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={speed === s}
              className={`h-10 px-3 text-sm font-semibold transition-colors ${
                speed === s ? "bg-ink text-surface" : "text-ink-2 hover:bg-canvas"
              }`}
              onClick={() => setSpeed(s)}
            >
              {s}×
            </button>
          ))}
        </div>
        <span className="font-mono text-sm text-ink-3">
          {processed} / {total} pedidos
        </span>
      </div>

      <Readout
        className="max-w-xl"
        items={[
          { label: "Costo acumulado", value: `${formatUsd1000(avgCost)} / 1000`, detail: "promedio de lo ruteado" },
          { label: "Calidad acumulada", value: formatQuality(quality), detail: "según la etiqueta de la fase 2" },
        ]}
      />

      {state.decisions.length === 0 ? (
        <p className="border border-dashed border-line px-4 py-5 text-sm text-ink-3">
          Reproducir o avanzar un paso para rutear los pedidos del corpus en orden fijo.
        </p>
      ) : (
        <ol className="m-0 list-none divide-y divide-line border-y border-line p-0" aria-label="Últimos pedidos ruteados">
          {state.decisions.map((d) => (
            <li key={d.index} className="flex items-center gap-4 py-2 text-sm">
              <span className="w-12 shrink-0 font-mono text-xs text-ink-3">#{d.index + 1}</span>
              <TierBadge tier={d.tier} className="w-24 shrink-0" />
              <span className="w-6 shrink-0 font-mono text-xs text-ink-3">{d.row.lang}</span>
              <span className="min-w-0 flex-1 truncate text-ink-2" title={d.row.text}>
                {d.row.text}
              </span>
              {d.ok ? (
                <Check className="size-4 shrink-0 text-ok" aria-label="suficiente" role="img" />
              ) : (
                <X className="size-4 shrink-0 text-danger" aria-label="insuficiente" role="img" />
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
