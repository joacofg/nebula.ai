"use client";

import { useMemo, useState } from "react";

import { useQuery } from "@tanstack/react-query";

import { ApplyTarget } from "@/components/evaluation/apply-target";
import {
  formatAhorro,
  formatQuality,
  formatRange,
  formatShare,
  formatTau,
  formatUsd1000,
} from "@/components/evaluation/format";
import { FrontierChart } from "@/components/evaluation/frontier-chart";
import { QualitySlider } from "@/components/evaluation/quality-slider";
import { ReplayFeed } from "@/components/evaluation/replay-feed";
import { TierShareBar } from "@/components/evaluation/tier-share-bar";
import { Figure } from "@/components/system/figure";
import { PageHeader } from "@/components/system/page-header";
import { Readout } from "@/components/system/readout";
import { ErrorAlert, LoadingRows } from "@/components/system/state";
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

const DEFAULT_TARGET = 0.95;
const REPLAY_SEED = 20260930;
const LANG_LABELS: Record<string, string> = { es: "Español", en: "Inglés" };

function prefersReducedMotion() {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

type CharacteristicRow = { parameter: string; condition: string; value: string; ci?: string; key?: boolean };

function CharacteristicsTable({ replay }: { replay: RouterReplay }) {
  const nested = replay.nested["0.95"] ?? null;
  const latency = Object.values(replay.latency).sort((a, b) => a.median_s - b.median_s);
  const rows: CharacteristicRow[] = nested
    ? [
        { parameter: "Ahorro vs todo frontier", condition: "cifra anidada", value: formatAhorro(nested.vs_all_frontier), ci: formatRange(nested.vs_all_frontier_ci95), key: true },
        { parameter: "Ahorro vs mezcla aleatoria", condition: "igual calidad", value: formatAhorro(nested.vs_random), ci: formatRange(nested.vs_random_ci95) },
        { parameter: "Calidad lograda", condition: "cifra anidada", value: formatQuality(nested.quality) },
        { parameter: "Costo", condition: "por 1000 pedidos", value: formatUsd1000(nested.cost) },
      ]
    : [];
  latency.forEach((l, i) =>
    rows.push({
      parameter: i === 0 ? "Latencia mediana" : "",
      condition: `${l.model} · n = ${l.n}`,
      value: `${l.median_s.toFixed(1)} s`,
    }),
  );

  const caption = "Características a calidad objetivo 0.95";
  return (
    <section aria-labelledby="characteristics-heading" className="flex flex-col gap-2">
      <h2 id="characteristics-heading" className="m-0 text-lg font-semibold text-ink">
        {caption}
      </h2>
      {nested ? null : <p className="text-sm text-ink-3">El replay no trae la cifra anidada para 0.95.</p>}
      <table aria-label={caption} className="w-full table-fixed border-collapse text-sm">
        <colgroup>
          <col className="w-[30%]" />
          <col className="w-[34%]" />
          <col className="w-[16%]" />
          <col className="w-[20%]" />
        </colgroup>
        <thead>
          <tr className="border-y-2 border-t-ink border-b-ink">
            <th scope="col" className="px-2 py-1.5 text-left font-label text-[13px] font-semibold">Parámetro</th>
            <th scope="col" className="px-2 py-1.5 text-left font-label text-[13px] font-semibold">Condición</th>
            <th scope="col" className="px-2 py-1.5 text-right font-label text-[13px] font-semibold">Valor</th>
            <th scope="col" className="px-2 py-1.5 text-left font-label text-[13px] font-semibold">IC 95 %</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.parameter}-${row.condition}`} className="border-b border-line">
              <th scope="row" className="px-2 py-2 text-left font-normal text-ink">{row.parameter}</th>
              <td className="px-2 py-2 font-label text-ink-3">{row.condition}</td>
              <td className={`px-2 py-2 text-right font-semibold whitespace-nowrap text-ink ${row.key ? "text-xl" : ""}`}>{row.value}</td>
              <td className="px-2 py-2 font-label whitespace-nowrap text-ink-3">{row.ci ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="m-0 text-[13px] text-ink-3">Cifra de la tesis: umbrales elegidos sin ver los pedidos evaluados (validación cruzada anidada).</p>
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
  const randomDetail =
    randomCost === null
      ? "ninguna mezcla alcanza esta calidad"
      : randomCost === 0
        ? "la mezcla aleatoria no cuesta nada a esta calidad"
        : `mezcla a la misma calidad: ${formatUsd1000(randomCost)}`;

  const langs = Object.entries(result.byLang).sort(([a], [b]) => b.localeCompare(a));

  return (
    <div className="flex flex-col gap-10 px-6 py-6">
      <div className="grid border border-line xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="min-w-0 border-line p-4 xl:border-r">
          <Figure number={1} caption="Calidad en función del costo. Cada vértice es un par de umbrales (τ local, τ economy); arriba a la izquierda es mejor.">
            <FrontierChart
              front={front}
              random={random}
              baselines={replay.baselines}
              current={{ cost: result.costPerPrompt, quality: result.quality }}
            />
          </Figure>
        </div>
        <div className="flex flex-col gap-5 border-t border-line p-5 xl:border-t-0">
          <QualitySlider value={target} onChange={setTarget} />
          <Readout
            items={[
              { label: "Costo por 1000 pedidos", value: formatUsd1000(result.costPerPrompt), emphasis: true },
              { label: "Calidad medida", value: formatQuality(result.quality), emphasis: true },
              { label: "Ahorro vs todo frontier", value: formatAhorro(vsFrontier) },
              { label: "Ahorro vs mezcla aleatoria", value: formatAhorro(vsRandom), detail: randomDetail },
              {
                label: "Umbrales τ local · economy",
                value: allFrontier ? "todo frontier (∞ · ∞)" : `${formatTau(point.tau_local)} · ${formatTau(point.tau_economy)}`,
              },
              ...langs.map(([lang, figure]) => ({
                label: `${LANG_LABELS[lang] ?? lang} · ${figure.n}`,
                value: `${formatQuality(figure.quality)} · ${formatUsd1000(figure.costPerPrompt)}`,
              })),
            ]}
          />
          <div className="flex flex-col gap-2">
            <div className="font-label text-[13px] font-medium text-ink-2">Reparto por nivel</div>
            <TierShareBar share={result.share} />
          </div>
          <ApplyTarget adminKey={adminKey} target={target} />
        </div>
      </div>

      <CharacteristicsTable replay={replay} />

      <section aria-labelledby="replay-heading" className="flex flex-col gap-3">
        <h2 id="replay-heading" className="m-0 text-lg font-semibold text-ink">
          Replay acelerado · {replay.rows.length} pedidos, {formatShare(result.share.local)} local
        </h2>
        <Figure number={2} caption="Cada pedido se rutea con el punto elegido; ✓ / ✗ indica si los jueces aceptaron la respuesta de ese nivel.">
          <ReplayFeed rows={replay.rows} order={order} point={point} initialPlaying={initialPlaying} />
        </Figure>
      </section>

      <p className="m-0 max-w-[75ch] text-[13px] text-ink-3">
        Corpus derivado de Dolly (CC BY-SA 3.0), GSM8K (MIT) y MBPP (CC BY 4.0); predicciones del router{" "}
        {replay.router_label} sobre pedidos que no vio al entrenar.
      </p>
    </div>
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
  const replay = replayQuery.data;
  const counts = replay
    ? replay.rows.reduce<Record<string, number>>((acc, r) => ({ ...acc, [r.lang]: (acc[r.lang] ?? 0) + 1 }), {})
    : null;

  return (
    <section>
      <PageHeader
        title="Evaluación del router"
        cells={[
          { label: "Router", value: `${replay?.router_label ?? "v1"} · 3 niveles` },
          { label: "Corpus", value: replay ? `${replay.rows.length} pedidos` : "—" },
          { label: "Idiomas", value: counts ? `${counts.es ?? 0} es · ${counts.en ?? 0} en` : "—" },
          { label: "Ejecución", value: "Sin red ni Ollama" },
        ]}
      />

      {replayQuery.isLoading ? (
        <div className="px-6 py-6">
          <LoadingRows rows={8} label="Cargando el replay del router" />
        </div>
      ) : replayQuery.isError ? (
        <div className="px-6 py-6">
          <ErrorAlert error={replayQuery.error} fallback="No se pudo cargar el replay del router." />
        </div>
      ) : replay ? (
        <EvaluationBody replay={replay} adminKey={adminKey ?? ""} />
      ) : (
        <div className="px-6 py-8">
          <p className="m-0 text-lg font-semibold text-ink">No hay replay del router.</p>
          <p className="mt-2 text-sm text-ink-2">
            Generarlo con <code className="font-mono text-[13px]">python -m scripts.router.train</code> o apuntar{" "}
            <code className="font-mono text-[13px]">NEBULA_ROUTER_REPLAY_PATH</code> a uno existente.
          </p>
        </div>
      )}
    </section>
  );
}
