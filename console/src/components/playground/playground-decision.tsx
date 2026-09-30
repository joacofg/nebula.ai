import type { UsageLedgerRecord } from "@/lib/admin-api";

type PlaygroundDecisionProps = {
  entry: UsageLedgerRecord;
  /** `X-Nebula-Route-Tier` from the live response; empty when the gateway sent none. */
  routeTier: string;
};

type Signals = Record<string, unknown>;

type Explanation =
  | { kind: "learned"; tier: string; version: string; steps: string[]; note: string | null }
  | { kind: "embedding_unavailable"; status: string; detail: string }
  | { kind: "heuristic"; detail: string }
  | { kind: "none" };

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/** Up to four decimals, never fewer than two: 0.9 → "0.90", 0.8312 → "0.8312". */
function formatProb(value: number) {
  const fixed = value.toFixed(4).replace(/0+$/, "");
  const [whole, decimals = ""] = fixed.split(".");
  return `${whole}.${decimals.padEnd(2, "0")}`;
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
  if (!signals) {
    return { kind: "none" };
  }
  const learned = typeof signals.learned_router === "string" ? signals.learned_router : null;

  if (entry.route_reason !== "learned_router") {
    if (learned) {
      return {
        kind: "embedding_unavailable",
        status: learned,
        detail: heuristicDetail(signals),
      };
    }
    return { kind: "heuristic", detail: heuristicDetail(signals) };
  }

  const pLocal = asNumber(signals.p_local) ?? 0;
  const pEconomy = asNumber(signals.p_economy) ?? 0;
  const target = asNumber(signals.quality_target);
  const point = (signals.operating_point ?? {}) as Signals;
  const tauLocal = asNumber(point.tau_local);
  const tauEconomy = asNumber(point.tau_economy);
  const allFrontier = tauLocal === null && tauEconomy === null;
  const targetText =
    target === null ? "" : ` (objetivo ${formatProb(target)}${allFrontier ? ", todo frontier" : ""})`;

  const clearsLocal = tauLocal !== null && pLocal >= tauLocal;
  const clearsEconomy = tauEconomy !== null && pEconomy >= tauEconomy;
  const steps: string[] = [];
  if (clearsLocal) {
    steps.push(`p_local ${formatProb(pLocal)} ≥ τ_local ${formatThreshold(tauLocal)} → local${targetText}`);
  } else {
    steps.push(`p_local ${formatProb(pLocal)} < τ_local ${formatThreshold(tauLocal)} → no alcanza el local`);
    steps.push(
      clearsEconomy
        ? `p_economy ${formatProb(pEconomy)} ≥ τ_economy ${formatThreshold(tauEconomy)} → economy${targetText}`
        : `p_economy ${formatProb(pEconomy)} < τ_economy ${formatThreshold(tauEconomy)} → frontier${targetText}`,
    );
  }

  const computed = clearsLocal ? "local" : clearsEconomy ? "economy" : "frontier";
  const tier = typeof signals.tier === "string" ? signals.tier : routeTier || computed;
  const note =
    computed === "economy" && tier === "frontier"
      ? "El router eligió economy, pero sin modelo economy configurado el gateway lo sirvió con frontier."
      : null;

  return { kind: "learned", tier, version: learned ?? "desconocido", steps, note };
}

export function PlaygroundDecision({ entry, routeTier }: PlaygroundDecisionProps) {
  const explanation = explainDecision(entry, routeTier);

  return (
    <section className="panel space-y-4 px-6 py-5" aria-labelledby="playground-decision-heading">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Decisión</div>
        <h3
          id="playground-decision-heading"
          className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950"
        >
          Por qué este nivel
        </h3>
      </div>

      {explanation.kind === "learned" ? (
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
                className="rounded-xl border border-border bg-slate-50 px-4 py-2.5 font-mono text-sm text-slate-900 [overflow-wrap:anywhere]"
              >
                {step}
              </li>
            ))}
          </ol>
          {explanation.note ? <p className="text-sm text-amber-900">{explanation.note}</p> : null}
          <p className="text-xs text-slate-500">
            Regla del gateway: el punto de operación más barato con calidad ≥ objetivo; luego p_local ≥ τ_local → local,
            si no p_economy ≥ τ_economy → economy, si no frontier.
          </p>
        </div>
      ) : explanation.kind === "embedding_unavailable" ? (
        <p className="text-sm text-slate-700">
          El router aprendido no pudo calcular el embedding del prompt ({explanation.status}), así que decidió la
          heurística token_complexity{explanation.detail}.
        </p>
      ) : explanation.kind === "heuristic" ? (
        <p className="text-sm text-slate-700">
          Ruteo heurístico (token_complexity){explanation.detail}: el router aprendido no estuvo activo para esta request.
        </p>
      ) : (
        <p className="text-sm text-slate-700">
          El ledger no registró señales de ruteo para esta request (por ejemplo, un acierto de caché o minimización
          estricta de metadatos).
        </p>
      )}
    </section>
  );
}
