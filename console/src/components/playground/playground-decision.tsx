import { DecisionPath, formatProb, type DecisionStep } from "@/components/system/decision-path";
import { Figure } from "@/components/system/figure";
import { complexityLabel, routerLabel } from "@/components/system/labels";
import { TierBadge } from "@/components/system/tier-badge";
import type { UsageLedgerRecord } from "@/lib/admin-api";

type PlaygroundDecisionProps = {
  entry: UsageLedgerRecord;
  /** `X-Nebula-Route-Tier` from the live response; empty when the gateway sent none. */
  routeTier: string;
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

function heuristicDetail(signals: Signals | null) {
  const tokens = asNumber(signals?.token_count);
  const complexity = typeof signals?.complexity_tier === "string" ? signals.complexity_tier : null;
  const parts = [
    tokens !== null ? `${tokens} tokens` : null,
    complexity ? `complejidad ${complexityLabel(complexity)}` : null,
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

  const clearsLocal = tauLocal !== null && pLocal !== null && pLocal >= tauLocal;
  const clearsEconomy = tauEconomy !== null && pEconomy !== null && pEconomy >= tauEconomy;

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

  return { kind: "learned", tier, computed, version, path, context, note, fallback };
}

export function PlaygroundDecision({ entry, routeTier, compact = false }: PlaygroundDecisionProps) {
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
          <Figure caption={`Cascada de decisión del router para este pedido. ${explanation.context}.`}>
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
          . Decidió: {routerLabel("token_complexity")}
          {explanation.detail}.
          {explanation.fallback ? " Después falló el modelo local y se sirvió con premium (fallback)." : ""}
        </p>
      ) : explanation.kind === "heuristic" ? (
        <p className="m-0 text-sm text-ink-2">
          {routerLabel("token_complexity")}
          {explanation.detail}: el router aprendido no estuvo activo.
          {explanation.fallback ? " Falló el modelo local y se sirvió con premium (fallback)." : ""}
        </p>
      ) : (
        <p className="m-0 text-sm text-ink-2">El ledger no registró señales de ruteo para este pedido.</p>
      )}
    </section>
  );
}
