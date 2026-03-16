type RuntimeHealthCardsProps = {
  dependencies: Record<string, { status: string; required: boolean; detail: string }>;
  isLoading: boolean;
};

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
        {entries.map(([name, dependency]) => (
          <article key={name} className="panel px-6 py-5">
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">{name}</div>
            <div className="mt-3 text-lg font-semibold text-slate-950">{dependency.status}</div>
            <p className="mt-2 text-sm text-slate-600">{dependency.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
