import type { UsageLedgerRecord } from "@/lib/admin-api";

import { Readout } from "@/components/system/readout";

type PlaygroundRecordedOutcomeProps = {
  entry: UsageLedgerRecord;
};

function orDash(value: string | null) {
  return value && value.trim().length > 0 ? value : "—";
}

export function PlaygroundRecordedOutcome({ entry }: PlaygroundRecordedOutcomeProps) {
  return (
    <section aria-labelledby="playground-ledger-heading" className="flex flex-col gap-2">
      <h2 id="playground-ledger-heading" className="m-0 text-lg font-semibold text-ink">
        Registro en el ledger
      </h2>
      <Readout
        items={[
          { label: "Costo estimado", value: entry.estimated_cost === null ? "—" : `USD ${entry.estimated_cost.toFixed(4)}`, emphasis: true },
          { label: "Tokens", value: `${entry.prompt_tokens} + ${entry.completion_tokens} = ${entry.total_tokens}` },
          { label: "Modelo", value: <span className="font-mono text-[13px] [overflow-wrap:anywhere]">{orDash(entry.response_model)}</span> },
          { label: "Proveedor", value: orDash(entry.final_provider) },
          { label: "Ruta", value: entry.final_route_target },
          { label: "Motivo", value: orDash(entry.route_reason) },
          { label: "Estado", value: entry.terminal_status },
          { label: "Política", value: <span className="font-mono text-[12px] font-normal">{orDash(entry.policy_outcome)}</span> },
          { label: "Caché", value: entry.cache_hit ? "sí" : "no" },
          { label: "Fallback", value: entry.fallback_used ? "sí" : "no" },
        ]}
      />
    </section>
  );
}
