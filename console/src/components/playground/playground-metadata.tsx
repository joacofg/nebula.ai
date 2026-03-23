type PlaygroundMetadataProps = {
  requestId: string;
  tenantId: string;
  routeTarget: string;
  routeReason: string;
  provider: string;
  cacheHit: boolean;
  fallbackUsed: boolean;
  latencyMs: number;
  policyMode: string;
  policyOutcome: string;
};

function yesNo(value: boolean) {
  return value ? "Yes" : "No";
}

function displayValue(value: string) {
  return value.trim().length > 0 ? value : "N/A";
}

export function PlaygroundMetadata({
  requestId,
  tenantId,
  routeTarget,
  routeReason,
  provider,
  cacheHit,
  fallbackUsed,
  latencyMs,
  policyMode,
  policyOutcome,
}: PlaygroundMetadataProps) {
  return (
    <section className="panel space-y-4 px-6 py-5">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Metadata</div>
        <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
          Immediate response evidence
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          These fields describe the live route, policy, and tenant evidence before the ledger finishes
          recording the same request.
        </p>
      </div>

      <dl className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetadataRow label="Request ID" value={displayValue(requestId)} mono />
        <MetadataRow label="Tenant" value={displayValue(tenantId)} mono />
        <MetadataRow label="Route target" value={displayValue(routeTarget)} />
        <MetadataRow label="Route reason" value={displayValue(routeReason)} />
        <MetadataRow label="Provider" value={displayValue(provider)} />
        <MetadataRow label="Policy mode" value={displayValue(policyMode)} />
        <MetadataRow label="Policy outcome" value={displayValue(policyOutcome)} />
        <MetadataRow label="Cache hit" value={yesNo(cacheHit)} />
        <MetadataRow label="Fallback used" value={yesNo(fallbackUsed)} />
        <MetadataRow label="Latency" value={`${latencyMs} ms`} />
      </dl>
    </section>
  );
}

function MetadataRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-border bg-white px-4 py-4">
      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</dt>
      <dd className={["mt-2 text-sm text-slate-900", mono ? "font-[var(--font-fira-code)]" : ""].join(" ")}>
        {value}
      </dd>
    </div>
  );
}
