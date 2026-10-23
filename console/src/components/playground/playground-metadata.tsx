import { Readout } from "@/components/system/readout";

type PlaygroundMetadataProps = {
  requestId: string;
  tenantId: string;
  policyMode: string;
  policyOutcome: string;
};

function orDash(value: string) {
  return value.trim().length > 0 ? value : "—";
}

/**
 * What only the live response carries: the request id and the policy that applied. Route, reason,
 * tier, provider, cache, fallback and latency are the ledger block's, which records them once.
 */
export function PlaygroundMetadata(props: PlaygroundMetadataProps) {
  return (
    <details className="group border-t border-line pt-3">
      <summary className="cursor-pointer text-sm font-semibold text-ink marker:text-ink-3">Detalle de la respuesta</summary>
      <Readout
        className="mt-3"
        items={[
          { label: "Request ID", value: <span className="font-mono text-[13px] [overflow-wrap:anywhere]">{orDash(props.requestId)}</span> },
          { label: "Tenant", value: <span className="font-mono text-[13px]">{orDash(props.tenantId)}</span> },
          { label: "Modo de política", value: orDash(props.policyMode) },
          { label: "Resultado de política", value: <span className="font-mono text-[12px] font-normal">{orDash(props.policyOutcome)}</span> },
        ]}
      />
    </details>
  );
}
