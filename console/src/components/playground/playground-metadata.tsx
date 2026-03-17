type PlaygroundMetadataProps = {
  requestId: string;
  routeTarget: string;
  provider: string;
  cacheHit: boolean;
  fallbackUsed: boolean;
  latencyMs: number;
  policyOutcome: string;
};

function yesNo(value: boolean) {
  return value ? "Yes" : "No";
}

export function PlaygroundMetadata({
  requestId,
  routeTarget,
  provider,
  cacheHit,
  fallbackUsed,
  latencyMs,
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
          These fields describe the live response before the ledger finishes recording the same request.
        </p>
      </div>

      <dl className="grid gap-4 sm:grid-cols-2">
        <MetadataRow label="Request ID" value={requestId} mono />
        <MetadataRow label="Route target" value={routeTarget} />
        <MetadataRow label="Provider" value={provider} />
        <MetadataRow label="Cache hit" value={yesNo(cacheHit)} />
        <MetadataRow label="Fallback" value={yesNo(fallbackUsed)} />
        <MetadataRow label="Latency" value={`${latencyMs} ms`} />
        <MetadataRow label="Policy outcome" value={policyOutcome} />
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
