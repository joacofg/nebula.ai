import { RuntimeHealthDependency } from "@/lib/admin-api";

type RuntimeHealthCardsProps = {
  dependencies: Record<string, RuntimeHealthDependency>;
  isLoading: boolean;
};

function formatHealthValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "N/A";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return String(value);
}

function formatHealthLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function buildMetadata(dependency: RuntimeHealthDependency): Array<[string, unknown]> {
  const metadata: Array<[string, unknown]> = [
    ["Dependency class", dependency.dependency_class],
    ["Lifecycle state", dependency.lifecycle_state],
    ["Serving effect", dependency.serving_effect],
    ["Reason code", dependency.reason_code],
    ["Enabled", dependency.enabled],
    ["Recovering", dependency.recovering],
    ["Last failure", dependency.last_failure_at],
    ["Last recovery", dependency.last_recovery_at],
    ["Last status", dependency.last_status],
    ["Last run", dependency.last_run_at],
    ["Last attempt", dependency.last_attempted_run_at],
    ["Deleted rows", dependency.last_deleted_count],
    ["Eligible rows", dependency.last_eligible_count],
    ["Last cutoff", dependency.last_cutoff],
    ["Last error", dependency.last_error],
  ];

  return metadata.filter(([, value]) => value !== undefined);
}

export function RuntimeHealthCards({ dependencies, isLoading }: RuntimeHealthCardsProps) {
  if (isLoading) {
    return <div className="panel px-6 py-5 text-sm text-ink-4">Loading dependency health...</div>;
  }

  const entries = Object.entries(dependencies);
  const hasOptionalDegradation = entries.some(
    ([, dependency]) => dependency.required === false && dependency.status === "degraded",
  );

  return (
    <section className="space-y-4">
      {hasOptionalDegradation ? (
        <div className="rounded-xl border border-warn-line bg-warn-soft px-6 py-4 text-sm text-warn">
          Optional dependency degradation does not block gateway readiness.
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {entries.map(([name, dependency]) => {
          const metrics = buildMetadata(dependency);

          return (
            <article key={name} className="panel px-6 py-5">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">{name}</div>
              <div className="mt-3 text-lg font-semibold text-ink">
                {formatHealthLabel(dependency.status)}
              </div>
              <p className="mt-2 text-sm text-ink-3">{dependency.detail}</p>
              {metrics.length > 0 ? (
                <dl className="mt-4 grid gap-3">
                  {metrics.map(([label, value]) => (
                    <div key={`${name}-${label}`} className="rounded-xl border border-line bg-canvas px-4 py-3">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">{label}</dt>
                      <dd className="mt-2 text-sm font-medium text-ink wrap-anywhere">
                        {typeof value === "string" ? formatHealthLabel(value) : formatHealthValue(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
