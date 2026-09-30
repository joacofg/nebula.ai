import { DecisionPath, type DecisionStep } from "@/components/system/decision-path";
import { Figure } from "@/components/system/figure";
import { TierBadge } from "@/components/system/tier-badge";
import type { UsageLedgerRecord } from "@/lib/admin-api";

type PlaygroundDecisionProps = {
  entry: UsageLedgerRecord;
  /** `X-Nebula-Route-Tier` from the live response; empty when the gateway sent none. */
  routeTier: string;
  /** Figure number for the decision path caption on the page that shows it. */
  figureNumber?: number;
  /** Narrow column (the ledger detail): draw the path in its compact layout. */
  compact?: boolean;
};

type Signals = Record<string, unknown>;

type Explanation =
  | { kind: "cache"; score: number | null }
  | {
      kind: "learned";
      tier: string;
      computed: "local" | "economy" | "frontier";
      version: string;
      steps: string[];
      path: DecisionStep[];
      context: string;
      note: string | null;
      fallback: boolean;
    }
  | { kind: "embedding_unavailable"; status: string; detail: string; fallback: boolean }
  | { kind: "heuristic"; detail: string; fallback: boolean }
  | { kind: "none" };

const EMBEDDING_STATUSES = new Set(["embedding_unavailable", "embedding_dimension_mismatch"]);

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/** Up to four decimals, never fewer than two: 0.9 → "0.90", 0.8312 → "0.8312". */
function formatProb(value: number) {
  const fixed = value.toFixed(4).replace(/0+$/, "");
  const [whole, decimals = ""] = fixed.split(".");
  return `${whole}.${decimals.padEnd(2, "0")}`;
}

function formatMaybe(value: number | null) {
  return value === null ? "—" : formatProb(value);
}

function formatThreshold(value: number | null) {
  return value === null ? "∞" : formatProb(value);
}

function heuristicDetail(signals: Signals | null) {
  const tokens = asNumber(signals?.token_count);
  const complexity = typeof signals?.complexity_tier === "string" ? signals.complexity_tier : null;
  const parts = [
    tokens !== null ? `${tokens} tokens` : null,
    complexity ? `complejidad ${complexity}` : null,
    signals?.keyword_match === true ? "con palabra clave" : null,
  ].filter(Boolean);
  return parts.length ? ` (${parts.join(", ")})` : "";
}

export function explainDecision(entry: UsageLedgerRecord, routeTier: string): Explanation {
  const signals = (entry.route_signals ?? null) as Signals | null;
  // The ledger keeps the routing signals even when the answer came from elsewhere,
  // so the reason decides what to explain, not the signals.
  if (entry.route_reason === "cache_hit") {
    return { kind: "cache", score: asNumber(signals?.cache_similarity_score) };
  }
  if (!signals) {
    return { kind: "none" };
  }
  const fallback = entry.fallback_used || entry.route_reason?.endsWith("_fallback") === true;
  const learned = typeof signals.learned_router === "string" ? signals.learned_router : null;
  const learnedDecided =
    entry.route_reason === "learned_router" || (fallback && learned !== null && !EMBEDDING_STATUSES.has(learned));

  if (!learnedDecided) {
    if (learned && EMBEDDING_STATUSES.has(learned)) {
      return { kind: "embedding_unavailable", status: learned, detail: heuristicDetail(signals), fallback };
    }
    return { kind: "heuristic", detail: heuristicDetail(signals), fallback };
  }

  const pLocal = asNumber(signals.p_local);
  const pEconomy = asNumber(signals.p_economy);
  const target = asNumber(signals.quality_target);
  const point = (signals.operating_point ?? {}) as Signals;
  const tauLocal = asNumber(point.tau_local);
  const tauEconomy = asNumber(point.tau_economy);
  const allFrontier = tauLocal === null && tauEconomy === null;
  const targetText =
    target === null ? "" : ` (objetivo ${formatProb(target)}${allFrontier ? ", todo frontier" : ""})`;

  const clearsLocal = tauLocal !== null && pLocal !== null && pLocal >= tauLocal;
  const clearsEconomy = tauEconomy !== null && pEconomy !== null && pEconomy >= tauEconomy;
  const steps: string[] = [];
  if (clearsLocal) {
    steps.push(`p_local ${formatMaybe(pLocal)} ≥ τ_local ${formatThreshold(tauLocal)} → local${targetText}`);
  } else {
    steps.push(
      pLocal === null
        ? `p_local — (no registrado) → no se puede comparar con τ_local ${formatThreshold(tauLocal)}`
        : `p_local ${formatMaybe(pLocal)} < τ_local ${formatThreshold(tauLocal)} → no alcanza el local`,
    );
    steps.push(
      pEconomy === null
        ? `p_economy — (no registrado) → no se puede comparar con τ_economy ${formatThreshold(tauEconomy)}`
        : clearsEconomy
          ? `p_economy ${formatMaybe(pEconomy)} ≥ τ_economy ${formatThreshold(tauEconomy)} → economy${targetText}`
          : `p_economy ${formatMaybe(pEconomy)} < τ_economy ${formatThreshold(tauEconomy)} → frontier${targetText}`,
    );
  }

  const computed = clearsLocal ? "local" : clearsEconomy ? "economy" : "frontier";
  const tier = typeof signals.tier === "string" ? signals.tier : routeTier || computed;
  const note =
    computed === "economy" && tier === "frontier"
      ? "El router eligió economy, pero sin modelo economy configurado el gateway lo sirvió con frontier."
      : null;

  const path: DecisionStep[] = [
    { tier: "local", p: pLocal, tau: tauLocal },
    { tier: "economy", p: pEconomy, tau: tauEconomy },
  ];
  const version = learned ?? "desconocido";
  const context = [
    target === null ? null : `Objetivo ${formatProb(target)}`,
    target !== null && allFrontier ? "todo frontier" : null,
    `router aprendido ${version}`,
  ]
    .filter(Boolean)
    .join(" · ");

  return { kind: "learned", tier, computed, version, steps, path, context, note, fallback };
}

export function PlaygroundDecision({ entry, routeTier, figureNumber = 1, compact = false }: PlaygroundDecisionProps) {
  const explanation = explainDecision(entry, routeTier);

  return (
    <section className="flex flex-col gap-3" aria-labelledby="playground-decision-heading">
      <div className="flex items-baseline justify-between gap-4">
        <h2 id="playground-decision-heading" className="m-0 text-lg font-semibold text-ink">
          Por qué este nivel
        </h2>
        {explanation.kind === "learned" ? <TierBadge tier={explanation.tier} /> : null}
      </div>

      {explanation.kind === "cache" ? (
        <p className="m-0 text-sm text-ink-2">
          Respuesta servida desde el caché semántico
          {explanation.score !== null ? ` (similitud ${formatProb(explanation.score)})` : ""}: no se llamó a ningún
          modelo.
        </p>
      ) : explanation.kind === "learned" ? (
        <>
          <Figure number={figureNumber} caption={`Cascada de decisión del router para este pedido. ${explanation.context}.`}>
            <DecisionPath steps={explanation.path} chosen={explanation.computed} animate compact={compact} />
          </Figure>
          {explanation.note ? <p className="m-0 text-sm text-warn">{explanation.note}</p> : null}
          {explanation.fallback ? (
            <p className="m-0 text-sm text-warn">Falló el modelo local y se sirvió con el proveedor premium (fallback).</p>
          ) : null}
        </>
      ) : explanation.kind === "embedding_unavailable" ? (
        <p className="m-0 text-sm text-ink-2">
          {explanation.status === "embedding_dimension_mismatch"
            ? "El embedding del prompt no tiene la dimensión que espera el router aprendido"
            : "El router aprendido no pudo calcular el embedding del prompt"}
          ; decidió la heurística token_complexity{explanation.detail}.
          {explanation.fallback ? " Después falló el modelo local y se sirvió con premium (fallback)." : ""}
        </p>
      ) : explanation.kind === "heuristic" ? (
        <p className="m-0 text-sm text-ink-2">
          Ruteo heurístico (token_complexity){explanation.detail}: el router aprendido no estuvo activo.
          {explanation.fallback ? " Falló el modelo local y se sirvió con premium (fallback)." : ""}
        </p>
      ) : (
        <p className="m-0 text-sm text-ink-2">El ledger no registró señales de ruteo para este pedido.</p>
      )}
    </section>
  );
}
