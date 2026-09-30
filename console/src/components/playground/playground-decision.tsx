import type { UsageLedgerRecord } from "@/lib/admin-api";

type PlaygroundDecisionProps = {
  entry: UsageLedgerRecord;
  /** `X-Nebula-Route-Tier` from the live response; empty when the gateway sent none. */
  routeTier: string;
};

type Signals = Record<string, unknown>;

type Explanation =
  | { kind: "cache"; score: number | null }
  | { kind: "learned"; tier: string; version: string; steps: string[]; note: string | null; fallback: boolean }
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

  return { kind: "learned", tier, version: learned ?? "desconocido", steps, note, fallback };
}

export function PlaygroundDecision({ entry, routeTier }: PlaygroundDecisionProps) {
  const explanation = explainDecision(entry, routeTier);

  return (
    <section className="panel space-y-4 px-6 py-5" aria-labelledby="playground-decision-heading">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Decisión</div>
        <h3
          id="playground-decision-heading"
          className="mt-2 font-(--font-fira-code) text-xl font-semibold text-slate-950"
        >
          Por qué este nivel
        </h3>
      </div>

      {explanation.kind === "cache" ? (
        <p className="text-sm text-slate-700">
          Respuesta servida desde el caché semántico
          {explanation.score !== null ? ` (similitud ${formatProb(explanation.score)})` : ""}: no se llamó a ningún
          modelo, así que el nivel del router no se aplicó.
        </p>
      ) : explanation.kind === "learned" ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="rounded-full bg-slate-900 px-3 py-1 font-mono text-xs font-semibold text-white">
              Nivel: {explanation.tier}
            </span>
            <span className="text-slate-600">Router aprendido {explanation.version}</span>
          </div>
          <ol className="space-y-2">
            {explanation.steps.map((step) => (
              <li
                key={step}
                className="rounded-xl border border-border bg-slate-50 px-4 py-2.5 font-mono text-sm text-slate-900 wrap-anywhere"
              >
                {step}
              </li>
            ))}
          </ol>
          {explanation.note ? <p className="text-sm text-amber-900">{explanation.note}</p> : null}
          {explanation.fallback ? (
            <p className="text-sm text-amber-900">
              Falló el modelo local y la request se sirvió con el proveedor premium (fallback).
            </p>
          ) : null}
          <p className="text-xs text-slate-500">
            Regla del gateway: el punto de operación más barato con calidad ≥ objetivo; luego p_local ≥ τ_local → local,
            si no p_economy ≥ τ_economy → economy, si no frontier.
          </p>
        </div>
      ) : explanation.kind === "embedding_unavailable" ? (
        <p className="text-sm text-slate-700">
          {explanation.status === "embedding_dimension_mismatch"
            ? "El embedding del prompt no tiene la dimensión que espera el router aprendido"
            : "El router aprendido no pudo calcular el embedding del prompt"}
          , así que decidió la heurística token_complexity{explanation.detail}.
          {explanation.fallback ? " Después falló el modelo local y se sirvió con premium (fallback)." : ""}
        </p>
      ) : explanation.kind === "heuristic" ? (
        <p className="text-sm text-slate-700">
          Ruteo heurístico (token_complexity){explanation.detail}: el router aprendido no estuvo activo para esta request.
          {explanation.fallback ? " Falló el modelo local y se sirvió con premium (fallback)." : ""}
        </p>
      ) : (
        <p className="text-sm text-slate-700">
          El ledger no registró señales de ruteo para esta request (por ejemplo, con minimización estricta de
          metadatos).
        </p>
      )}
    </section>
  );
}
