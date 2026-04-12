type RuntimeHealthDependency = {
  status: string;
  required: boolean;
  detail: string;
  [key: string]: unknown;
};

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

export function RuntimeHealthCards({ dependencies, isLoading }: RuntimeHealthCardsProps) {
  if (isLoading) {
    return <div className="panel px-6 py-5 text-sm text-slate-500">Loading dependency health...</div>;
  }

  const entries = Object.entries(dependencies);
  const hasOptionalDegradation = entries.some(
    ([, dependency]) => dependency.required === false && dependency.status === "degraded",
  );

  return (
    <section className="space-y-4">
      {hasOptionalDegradation ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-6 py-4 text-sm text-amber-900">
          Optional dependency degradation does not block gateway readiness.
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {entries.map(([name, dependency]) => {
          const metrics = [
            ["Last status", dependency.last_status],
            ["Last run", dependency.last_run_at],
            ["Last attempt", dependency.last_attempted_run_at],
            ["Deleted rows", dependency.last_deleted_count],
            ["Eligible rows", dependency.last_eligible_count],
            ["Last error", dependency.last_error],
          ].filter(([, value]) => value !== undefined);

          return (
            <article key={name} className="panel px-6 py-5">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">{name}</div>
              <div className="mt-3 text-lg font-semibold text-slate-950">{dependency.status}</div>
              <p className="mt-2 text-sm text-slate-600">{dependency.detail}</p>
              {metrics.length > 0 ? (
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  {metrics.map(([label, value]) => (
                    <div key={`${name}-${label}`} className="rounded-xl border border-border bg-slate-50 px-4 py-3">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">{formatHealthValue(value)}</dd>
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
