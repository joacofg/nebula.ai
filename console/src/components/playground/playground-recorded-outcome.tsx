import type { UsageLedgerRecord } from "@/lib/admin-api";

import { formatLatency, rowTier } from "@/components/ledger/ledger-table";
import { reasonLabel, statusLabel } from "@/components/system/labels";
import { Readout } from "@/components/system/readout";
import { TierBadge } from "@/components/system/tier-badge";

type PlaygroundRecordedOutcomeProps = {
  entry: UsageLedgerRecord;
};

export function PlaygroundRecordedOutcome({ entry }: PlaygroundRecordedOutcomeProps) {
  return (
    <section aria-labelledby="playground-ledger-heading" className="flex flex-col gap-2">
      <h2 id="playground-ledger-heading" className="m-0 text-lg font-semibold text-ink">
        Registro en el ledger
      </h2>
      <Readout items={ledgerReadout(entry)} />
    </section>
  );
}

/** The ledger row as instrument readings, shared by Playground and Observabilidad. */
export function ledgerReadout(entry: UsageLedgerRecord) {
  return [
    { label: "Nivel", value: <TierBadge tier={rowTier(entry)} /> },
    { label: "Latencia", value: formatLatency(entry.latency_ms) },
    { label: "Modelo", value: <span className="font-mono text-[13px]">{entry.response_model || "—"}</span> },
    { label: "Costo estimado", value: entry.estimated_cost === null ? "—" : `USD ${entry.estimated_cost.toFixed(4)}` },
    { label: "Tokens", value: `${entry.prompt_tokens} + ${entry.completion_tokens} = ${entry.total_tokens}` },
    { label: "Proveedor", value: entry.final_provider || "—" },
    { label: "Ruta", value: entry.final_route_target },
    { label: "Motivo", value: <span title={entry.route_reason ?? ""}>{reasonLabel(entry.route_reason)}</span> },
    { label: "Estado", value: <span title={entry.terminal_status}>{statusLabel(entry.terminal_status)}</span> },
    { label: "Caché", value: entry.cache_hit ? "sí" : "no" },
    { label: "Fallback", value: entry.fallback_used ? "sí" : "no" },
  ];
}
