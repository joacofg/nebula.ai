import type { UsageLedgerRecord } from "@/lib/admin-api";

import { formatTimestamp } from "@/components/observability/format";
import { PlaygroundDecision } from "@/components/playground/playground-decision";
import { ledgerReadout } from "@/components/playground/playground-recorded-outcome";
import {
  complexityLabel,
  denialReasonLabel,
  enforcementLabel,
  governanceSourceLabel,
  messageTypeLabel,
  minimizationLabel,
  NO_SCORE_LABEL,
  reasonLabel,
  retentionWindowLabel,
  scoreLabel,
  scoreModeLabel,
  suppressedFieldLabel,
} from "@/components/system/labels";
import { Readout, type ReadoutItem } from "@/components/system/readout";
import { EmptyState } from "@/components/system/state";
import { formatUsdText } from "@/lib/format";

type RouteSignals = Record<string, unknown>;

type LedgerRequestDetailProps = {
  entry: UsageLedgerRecord | null;
};

type Section = { title: string; summary: string | null; items: ReadoutItem[] };

function orDash(value: string | null | undefined) {
  return value && value.length > 0 ? value : "—";
}

/** The reason of a denial in Spanish; the gateway's own sentence stays as the title when it was translated. */
function denialReason(text: string): ReadoutItem["value"] {
  const label = denialReasonLabel(text);
  return label === text ? label : <span title={text}>{label}</span>;
}

function yesNo(value: boolean) {
  return value ? "sí" : "no";
}

function asRouteSignals(value: UsageLedgerRecord["route_signals"]): RouteSignals | null {
  return value && typeof value === "object" ? value : null;
}

function formatScore(value: unknown) {
  const numericValue = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(numericValue)) {
    return null;
  }
  return numericValue.toFixed(2);
}

function budgetSection(policyOutcome: string | null | undefined): Section | null {
  if (!policyOutcome) {
    return null;
  }
  const items: ReadoutItem[] = [];
  let summary: string | null = null;

  const hard = policyOutcome.match(/hard_budget=exceeded\(limit_usd=([^,]+),spent_usd=([^,]+),enforcement=([^)]+)\)/);
  if (hard) {
    const [, limitUsd, spentUsd, enforcement] = hard;
    summary = "Presupuesto duro alcanzado";
    items.push({ label: "Gastado al decidir", value: formatUsdText(spentUsd) });
    items.push({ label: "Límite duro", value: formatUsdText(limitUsd) });
    items.push({ label: "Aplicación", value: enforcementLabel(enforcement) });
  }
  if (policyOutcome.includes("budget_action=downgraded_to_local")) {
    summary = "Premium degradado a local";
    items.push({ label: "Acción", value: "Degradado a local" });
  }
  const denied = policyOutcome.match(/(?:^|;)denied=([^;]+)/);
  if (denied) {
    summary = "Pedido premium denegado por presupuesto";
    items.push({ label: "Motivo de la denegación", value: denialReason(denied[1]) });
  } else if (policyOutcome.startsWith("Tenant hard budget limit reached; premium routing is blocked")) {
    summary = "Pedido premium denegado por presupuesto";
    items.push({ label: "Motivo de la denegación", value: denialReason(policyOutcome) });
    const spent = policyOutcome.match(/spent_usd=([^,)]+)/);
    const limit = policyOutcome.match(/limit_usd=([^)]+)/);
    if (spent) {
      items.push({ label: "Gastado al decidir", value: formatUsdText(spent[1]) });
    }
    if (limit) {
      items.push({ label: "Límite duro", value: formatUsdText(limit[1]) });
    }
  }
  if (policyOutcome.includes("soft_budget=exceeded")) {
    summary = summary ?? "Aviso de presupuesto blando";
    items.push({ label: "Presupuesto blando", value: "Superado (solo aviso)" });
  }
  return summary || items.length ? { title: "Presupuesto", summary, items } : null;
}

function routingState(signals: RouteSignals, routeReason: string | null, score: string | null) {
  const mode = typeof signals.route_mode === "string" ? signals.route_mode : null;
  // The words are the policy parity's: both pages say the same thing about the same row.
  if (mode === null && routeReason === "calibrated_routing_disabled") {
    return reasonLabel(routeReason);
  }
  const withScore = (label: string) => (score === null ? label : `${label} (${scoreLabel(score)})`);
  if (signals.degraded_routing === true || mode === "degraded") {
    return withScore(scoreModeLabel("degraded"));
  }
  if (signals.calibrated_routing === true || mode === "calibrated") {
    return withScore(scoreModeLabel("calibrated"));
  }
  return withScore(mode !== null ? scoreModeLabel(mode) : NO_SCORE_LABEL);
}

/** The v0 heuristic's score breakdown; absent for the learned router, which the decision path explains. */
function heuristicSection(signals: RouteSignals | null, routeReason: string | null): Section | null {
  if (!signals || (typeof signals.learned_router === "string" && routeReason === "learned_router")) {
    return null;
  }
  const components =
    signals.score_components && typeof signals.score_components === "object"
      ? (signals.score_components as Record<string, unknown>)
      : null;
  const score = (components ? formatScore(components.total_score) : null) ?? formatScore(signals.route_score);
  const items: ReadoutItem[] = [{ label: "Estado del ruteo", value: routingState(signals, routeReason, score) }];
  if (typeof signals.route_mode === "string") {
    items.push({ label: "Modo", value: scoreModeLabel(signals.route_mode) });
  }
  if (score !== null) {
    items.push({ label: "Puntaje", value: score });
  }
  if (components) {
    const parts: Array<[string, unknown]> = [
      ["Puntaje por tokens", components.token_score],
      ["Bono por palabra clave", components.keyword_bonus],
      ["Bono de política", components.policy_bonus],
    ];
    for (const [label, raw] of parts) {
      const value = formatScore(raw);
      if (value !== null) {
        items.push({ label, value });
      }
    }
  }
  return { title: "Ruteo heurístico", summary: null, items };
}

function signalsSection(signals: RouteSignals | null): Section | null {
  if (!signals) {
    return null;
  }
  const items: ReadoutItem[] = [];
  if (signals.token_count !== undefined) {
    items.push({ label: "Tokens contados", value: String(signals.token_count) });
  }
  if (signals.complexity_tier !== undefined) {
    items.push({ label: "Complejidad", value: complexityLabel(String(signals.complexity_tier)) });
  }
  if (signals.keyword_match !== undefined) {
    items.push({ label: "Palabra clave", value: yesNo(Boolean(signals.keyword_match)) });
  }
  if (signals.model_constraint !== undefined) {
    items.push({ label: "Restricción de modelo", value: yesNo(Boolean(signals.model_constraint)) });
  }
  return items.length ? { title: "Señales", summary: null, items } : null;
}

function EvidenceSection({ section }: { section: Section }) {
  return (
    <section className="flex flex-col gap-1.5">
      <h3 className="m-0 font-label text-[13px] font-semibold text-ink-2">{section.title}</h3>
      {section.summary ? <p className="m-0 text-sm font-medium text-ink">{section.summary}</p> : null}
      <Readout items={section.items} />
    </section>
  );
}

export function LedgerRequestDetail({ entry }: LedgerRequestDetailProps) {
  if (!entry) {
    return <EmptyState title="Elegir un pedido del ledger." />;
  }

  const signals = asRouteSignals(entry.route_signals);
  const suppressed = entry.metadata_fields_suppressed ?? [];
  const sections = [budgetSection(entry.policy_outcome), heuristicSection(signals, entry.route_reason), signalsSection(signals)].filter(
    (s): s is Section => s !== null,
  );

  return (
    <section aria-labelledby="ledger-detail-heading" className="flex flex-col gap-6">
      <div>
        <h2 id="ledger-detail-heading" className="m-0 text-lg font-semibold text-ink">
          Pedido <span className="font-mono text-[15px] font-medium">{entry.request_id.slice(0, 8)}</span>
        </h2>
        <div className="font-label text-[13px] text-ink-3">{formatTimestamp(entry.timestamp)}</div>
      </div>

      {signals || entry.route_reason === "cache_hit" ? (
        <PlaygroundDecision entry={entry} routeTier={typeof signals?.tier === "string" ? signals.tier : ""} compact />
      ) : null}

      <Readout items={ledgerReadout(entry)} />

      <details className="border-t border-line pt-3">
        <summary className="cursor-pointer text-sm font-semibold text-ink marker:text-ink-3">Evidencia completa</summary>
        <div className="mt-3 flex flex-col gap-5">
          <Readout
            items={[
              { label: "Request ID", value: <span className="font-mono text-[12px] font-normal">{entry.request_id}</span> },
              { label: "Tenant", value: <span className="font-mono text-[13px]">{entry.tenant_id}</span> },
              { label: "Tipo de mensaje", value: messageTypeLabel(entry.message_type) },
              { label: "Modelo pedido", value: <span className="font-mono text-[13px]">{entry.requested_model}</span> },
              { label: "Política", value: <span className="font-mono text-[12px] font-normal">{orDash(entry.policy_outcome)}</span> },
              { label: "Retención", value: retentionWindowLabel(entry.evidence_retention_window) },
              { label: "Vence", value: entry.evidence_expires_at ? formatTimestamp(entry.evidence_expires_at) : "—" },
              { label: "Minimización", value: minimizationLabel(entry.metadata_minimization_level) },
              { label: "Campos suprimidos", value: suppressed.length ? suppressed.map(suppressedFieldLabel).join(", ") : "ninguno" },
              { label: "Fuente de gobierno", value: governanceSourceLabel(entry.governance_source) },
            ]}
          />
          {sections.map((section) => (
            <EvidenceSection key={section.title} section={section} />
          ))}
        </div>
      </details>
    </section>
  );
}
