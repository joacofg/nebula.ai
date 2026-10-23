import { policyOutcomeLabel, reasonLabel, routeLabel, routingModeLabel } from "@/components/system/labels";
import { Readout, type ReadoutItem } from "@/components/system/readout";
import { TierBadge } from "@/components/system/tier-badge";

/** The routing facts the X-Nebula-* response headers carry. */
export type ResponseFacts = {
  routeTarget: string;
  routeReason: string;
  routeTier: string;
  provider: string;
  cacheHit: boolean;
  fallbackUsed: boolean;
};

type PlaygroundMetadataProps = {
  requestId: string;
  tenantId: string;
  policyMode: string;
  policyOutcome: string;
  /**
   * Given only while there is no ledger record to read them from (the lookup failed or found
   * nothing): the ledger block records route, reason, tier, provider, cache and fallback, so
   * with it they are shown there and not here.
   */
  response?: ResponseFacts;
};

function orDash(value: string) {
  return value.trim().length > 0 ? value : "—";
}

function yesNo(value: boolean) {
  return value ? "sí" : "no";
}

function responseFacts(facts: ResponseFacts): ReadoutItem[] {
  return [
    { label: "Ruta", value: routeLabel(facts.routeTarget) },
    { label: "Motivo", value: <span title={facts.routeReason}>{reasonLabel(facts.routeReason)}</span> },
    { label: "Nivel", value: facts.routeTier ? <TierBadge tier={facts.routeTier} /> : "—" },
    { label: "Proveedor", value: orDash(facts.provider) },
    { label: "Caché", value: yesNo(facts.cacheHit) },
    { label: "Fallback", value: yesNo(facts.fallbackUsed) },
  ];
}

/**
 * What only the live response carries: the request id and the policy that applied. Route, reason,
 * tier, provider, cache, fallback and latency are the ledger block's, which records them once;
 * the response headers stand in for them only when that record is not there.
 */
export function PlaygroundMetadata(props: PlaygroundMetadataProps) {
  const items: ReadoutItem[] = [
    { label: "Request ID", value: <span className="font-mono text-[13px] [overflow-wrap:anywhere]">{orDash(props.requestId)}</span> },
    { label: "Tenant", value: <span className="font-mono text-[13px]">{orDash(props.tenantId)}</span> },
    ...(props.response ? responseFacts(props.response) : []),
    { label: "Modo de política", value: routingModeLabel(props.policyMode) },
    { label: "Resultado de política", value: policyOutcomeLabel(props.policyOutcome) },
  ];

  return (
    <details className="group border-t border-line pt-3">
      <summary className="cursor-pointer text-sm font-semibold text-ink marker:text-ink-3">Detalle de la respuesta</summary>
      <Readout className="mt-3" items={items} />
    </details>
  );
}
