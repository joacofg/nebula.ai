"use client";

import { useMemo, useState, type ReactNode } from "react";

import { useQuery } from "@tanstack/react-query";

import { ApplyTarget } from "@/components/evaluation/apply-target";
import {
  formatCi,
  formatPer1000,
  formatQuality,
  formatSaving,
  formatShare,
  formatTau,
} from "@/components/evaluation/format";
import { FrontierChart } from "@/components/evaluation/frontier-chart";
import { QualitySlider } from "@/components/evaluation/quality-slider";
import { ReplayFeed } from "@/components/evaluation/replay-feed";
import { TierShareBar } from "@/components/evaluation/tier-share-bar";
import { getRouterEvaluation } from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
import {
  evaluate,
  isAllFrontier,
  operatingPoint,
  paretoFront,
  randomCostAtQuality,
  randomFrontier,
  replayOrder,
  type RouterReplay,
} from "@/lib/router-replay";
import { ErrorAlert } from "@/components/system/state";

const DEFAULT_TARGET = 0.95;
const REPLAY_SEED = 20260930;
const LANG_LABELS: Record<string, string> = { es: "Español", en: "Inglés" };

function prefersReducedMotion() {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">{children}</div>;
}

function StatCard({ label, value, detail }: { label: string; value: string; detail?: ReactNode }) {
  return (
    <div role="group" aria-label={label} className="rounded-xl border border-line bg-surface px-4 py-4">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-4">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-ink">{value}</div>
      {detail ? <div className="mt-1 text-xs text-ink-4">{detail}</div> : null}
    </div>
  );
}

function NestedHeader({ replay }: { replay: RouterReplay }) {
  const nested = replay.nested["0.95"] ?? null;
  const latency = Object.values(replay.latency).sort((a, b) => a.median_s - b.median_s);
  return (
    <section aria-label="Cifra anidada" className="panel px-6 py-5">
      <Eyebrow>Cifra anidada · objetivo 0.95</Eyebrow>
      {nested ? (
        <div className="mt-3 grid gap-4 sm:grid-cols-3">
          <div>
            <div className="text-3xl font-semibold text-ink">{formatSaving(nested.vs_all_frontier)}</div>
            <div className="text-sm text-ink-3">costo vs todo frontier</div>
            <div className="font-mono text-xs text-ink-4">{formatCi(nested.vs_all_frontier_ci95)}</div>
          </div>
          <div>
            <div className="text-3xl font-semibold text-ink">{formatSaving(nested.vs_random)}</div>
            <div className="text-sm text-ink-3">costo vs mezcla aleatoria de igual calidad</div>
            <div className="font-mono text-xs text-ink-4">{formatCi(nested.vs_random_ci95)}</div>
          </div>
          <div>
            <div className="text-3xl font-semibold text-ink">{formatQuality(nested.quality)}</div>
            <div className="text-sm text-ink-3">calidad lograda</div>
            <div className="font-mono text-xs text-ink-4">{formatPer1000(nested.cost)} / 1000 prompts</div>
          </div>
        </div>
      ) : (
        <p className="mt-2 text-sm text-ink-3">El replay no trae la cifra anidada para 0.95.</p>
      )}
      <p className="mt-4 max-w-3xl text-sm text-ink-3">
        Umbrales y pesos elegidos sin ver el fold ruteado: es la cifra que se reporta. El replay de abajo usa las
        probabilidades fuera de fold sobre el mismo corpus.
      </p>
      {latency.length ? (
        <div className="mt-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-4">
            Latencia mediana por modelo (30 prompts en español, secuencial)
          </div>
          <dl className="mt-2 flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {latency.map((l) => (
              <div key={l.model} className="flex items-baseline gap-2">
                <dt className="font-mono text-xs text-ink-3">{l.model}</dt>
                <dd className="font-semibold tabular-nums text-ink">{`${l.median_s.toFixed(1)} s`}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}
    </section>
  );
}

function EvaluationBody({ replay, adminKey }: { replay: RouterReplay; adminKey: string }) {
  const [target, setTarget] = useState(DEFAULT_TARGET);
  const [initialPlaying] = useState(() => !prefersReducedMotion());

  const front = useMemo(() => paretoFront(replay.operating_points), [replay]);
  const random = useMemo(() => randomFrontier(replay.baselines), [replay]);
  const order = useMemo(() => replayOrder(replay.rows, REPLAY_SEED), [replay]);

  const point = useMemo(() => operatingPoint(replay.operating_points, target), [replay, target]);
  const result = useMemo(() => evaluate(replay.rows, point), [replay, point]);
  const allFrontier = isAllFrontier(point);

  const frontierCost = replay.baselines.all_frontier.cost;
  const vsFrontier = frontierCost > 0 ? 1 - result.costPerPrompt / frontierCost : null;
  const randomCost = randomCostAtQuality(replay.baselines, result.quality);
  const vsRandom = randomCost && randomCost > 0 ? 1 - result.costPerPrompt / randomCost : null;

  return (
    <>
      <NestedHeader replay={replay} />

      <section className="panel space-y-6 px-6 py-5" aria-labelledby="frontier-heading">
        <div>
          <Eyebrow>Frontera costo / calidad</Eyebrow>
          <h2 id="frontier-heading" className="mt-2 font-(--font-fira-code) text-2xl font-semibold text-ink">
            Elegí la calidad; el router elige el punto más barato que la cumple
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-ink-3">
            Misma regla que el gateway: entre los puntos de operación con calidad ≥ objetivo, el de menor costo; un
            objetivo de 1.0 (o uno que ningún punto alcanza) manda todo a frontier. Luego, en cascada: p_local ≥ τ_local
            → local, si no p_economy ≥ τ_economy → economy, si no frontier.
          </p>
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(300px,1fr)]">
          <FrontierChart
            front={front}
            random={random}
            baselines={replay.baselines}
            current={{ cost: result.costPerPrompt, quality: result.quality }}
          />

          <div className="space-y-5">
            <QualitySlider value={target} onChange={setTarget} />
            <p className="font-mono text-xs text-ink-3">
              {allFrontier
                ? "Punto elegido: todo frontier (τ_local = ∞, τ_economy = ∞)"
                : `Punto elegido: τ_local ${formatTau(point.tau_local)} · τ_economy ${formatTau(point.tau_economy)}`}
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <StatCard label="Costo por 1000 prompts" value={formatPer1000(result.costPerPrompt)} detail="USD" />
              <StatCard label="Calidad" value={formatQuality(result.quality)} detail="share de respuestas suficientes" />
              <StatCard
                label="Ahorro vs todo frontier"
                value={formatSaving(vsFrontier)}
                detail={`todo frontier: ${formatPer1000(frontierCost)}`}
              />
              <StatCard
                label="Ahorro vs mezcla aleatoria"
                value={formatSaving(vsRandom)}
                detail={
                  randomCost !== null
                    ? `aleatoria a la misma calidad: ${formatPer1000(randomCost)}`
                    : "ninguna mezcla alcanza esa calidad"
                }
              />
            </div>
            <div>
              <div className="field-label">Reparto por nivel</div>
              <TierShareBar share={result.share} />
            </div>
            <div>
              <div className="field-label">Calidad por idioma</div>
              <dl className="grid grid-cols-2 gap-3">
                {Object.entries(result.byLang)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .reverse()
                  .map(([lang, figure]) => (
                    <div key={lang} className="rounded-xl border border-line px-4 py-3">
                      <dt className="text-xs text-ink-4">
                        {LANG_LABELS[lang] ?? lang} · {figure.n} prompts
                      </dt>
                      <dd className="mt-1 font-semibold text-ink">
                        {formatQuality(figure.quality)}{" "}
                        <span className="text-xs font-normal text-ink-4">
                          {formatPer1000(figure.costPerPrompt)} / 1000
                        </span>
                      </dd>
                    </div>
                  ))}
              </dl>
            </div>
          </div>
        </div>
      </section>

      <section className="panel space-y-4 px-6 py-5" aria-labelledby="replay-heading">
        <div>
          <Eyebrow>Replay acelerado</Eyebrow>
          <h2 id="replay-heading" className="mt-2 font-(--font-fira-code) text-2xl font-semibold text-ink">
            {replay.rows.length} prompts del corpus, sin llamar a ningún modelo
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-ink-3">
            Cada prompt se rutea con el punto de operación actual ({formatShare(result.share.local)} local hoy); ✓/✗ es
            la etiqueta de la fase 2 para el nivel elegido. Mover el slider re-rutea desde el prompt en curso.
          </p>
        </div>
        <ReplayFeed rows={replay.rows} order={order} point={point} initialPlaying={initialPlaying} />
      </section>

      <section className="panel space-y-4 px-6 py-5" aria-labelledby="apply-heading">
        <div>
          <Eyebrow>Aplicar</Eyebrow>
          <h2 id="apply-heading" className="mt-2 font-(--font-fira-code) text-2xl font-semibold text-ink">
            Usar este objetivo en un tenant
          </h2>
        </div>
        <ApplyTarget adminKey={adminKey} target={target} />
      </section>

      <p className="px-1 text-xs text-ink-4">
        El replay usa los prompts del corpus de evaluación (derivados de Dolly, CC BY-SA 3.0; GSM8K, MIT; MBPP, CC BY
        4.0), con probabilidades fuera de fold del router {replay.router_label}. La cifra a reportar es la anidada del
        encabezado, no la de este replay.
      </p>
    </>
  );
}

export default function EvaluationPage() {
  const { adminKey } = useAdminSession();
  const replayQuery = useQuery({
    queryKey: queryKeys.routerEvaluation,
    queryFn: () => getRouterEvaluation(adminKey ?? ""),
    enabled: Boolean(adminKey),
    staleTime: Number.POSITIVE_INFINITY,
  });

  return (
    <section className="space-y-6">
      <header className="panel px-6 py-5">
        <Eyebrow>Evaluación</Eyebrow>
        <h2 className="mt-2 font-(--font-fira-code) text-2xl font-semibold text-ink">
          Router aprendido: costo vs calidad
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-ink-3">
          Cómo reparte el router entre el modelo local, economy y frontier según la calidad que se le pide, medido sobre
          el corpus etiquetado de la tesis. Funciona sin Ollama ni red externa.
        </p>
      </header>

      {replayQuery.isLoading ? (
        <div className="panel px-6 py-5 text-sm text-ink-4">Cargando el replay del router…</div>
      ) : replayQuery.isError ? (
        <ErrorAlert error={replayQuery.error} fallback="No se pudo cargar el replay del router." />
      ) : replayQuery.data ? (
        <EvaluationBody replay={replayQuery.data} adminKey={adminKey ?? ""} />
      ) : (
        <div className="panel px-6 py-8 text-center">
          <h3 className="font-(--font-fira-code) text-lg font-semibold text-ink">No hay replay del router</h3>
          <p className="mx-auto mt-2 max-w-xl text-sm text-ink-3">
            El gateway no encontró el archivo de replay. Generalo con{" "}
            <code className="font-mono text-xs">python -m scripts.router.train</code> o apuntá{" "}
            <code className="font-mono text-xs">NEBULA_ROUTER_REPLAY_PATH</code> a uno existente.
          </p>
        </div>
      )}
    </section>
  );
}
