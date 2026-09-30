import { Readout } from "@/components/system/readout";
import { TierBadge } from "@/components/system/tier-badge";

type PlaygroundMetadataProps = {
  requestId: string;
  tenantId: string;
  routeTarget: string;
  routeReason: string;
  routeTier: string;
  provider: string;
  cacheHit: boolean;
  fallbackUsed: boolean;
  latencyMs: number;
  policyMode: string;
  policyOutcome: string;
};

function yesNo(value: boolean) {
  return value ? "sí" : "no";
}

function orDash(value: string) {
  return value.trim().length > 0 ? value : "—";
}

/** The live X-Nebula-* evidence, folded: the ledger block above carries the headline numbers. */
export function PlaygroundMetadata(props: PlaygroundMetadataProps) {
  return (
    <details className="group border-t border-line pt-3">
      <summary className="cursor-pointer text-sm font-semibold text-ink marker:text-ink-3">Detalle de la respuesta</summary>
      <Readout
        className="mt-3"
        items={[
          { label: "Request ID", value: <span className="font-mono text-[13px] [overflow-wrap:anywhere]">{orDash(props.requestId)}</span> },
          { label: "Tenant", value: <span className="font-mono text-[13px]">{orDash(props.tenantId)}</span> },
          { label: "Ruta", value: orDash(props.routeTarget) },
          { label: "Motivo", value: orDash(props.routeReason) },
          { label: "Nivel", value: props.routeTier ? <TierBadge tier={props.routeTier} /> : "—" },
          { label: "Proveedor", value: orDash(props.provider) },
          { label: "Modo de política", value: orDash(props.policyMode) },
          { label: "Resultado de política", value: <span className="font-mono text-[12px] font-normal">{orDash(props.policyOutcome)}</span> },
          { label: "Caché", value: yesNo(props.cacheHit) },
          { label: "Fallback", value: yesNo(props.fallbackUsed) },
          { label: "Latencia", value: `${props.latencyMs} ms` },
        ]}
      />
    </details>
  );
}
