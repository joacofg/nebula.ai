import { RuntimeHealthDependency } from "@/lib/admin-api";
import { Readout } from "@/components/system/readout";
import { EmptyState, LoadingRows } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";

type RuntimeHealthCardsProps = {
  dependencies: Record<string, RuntimeHealthDependency>;
  isLoading: boolean;
};

function formatHealthValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "sí" : "no";
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
    ["Clase", dependency.dependency_class],
    ["Ciclo de vida", dependency.lifecycle_state],
    ["Efecto", dependency.serving_effect],
    ["Código", dependency.reason_code],
    ["Activada", dependency.enabled],
    ["Recuperándose", dependency.recovering],
    ["Última falla", dependency.last_failure_at],
    ["Última recuperación", dependency.last_recovery_at],
    ["Último estado", dependency.last_status],
    ["Última corrida", dependency.last_run_at],
    ["Último intento", dependency.last_attempted_run_at],
    ["Filas borradas", dependency.last_deleted_count],
    ["Filas elegibles", dependency.last_eligible_count],
    ["Último corte", dependency.last_cutoff],
    ["Último error", dependency.last_error],
  ];

  return metadata.filter(([, value]) => value !== undefined);
}

export function RuntimeHealthCards({ dependencies, isLoading }: RuntimeHealthCardsProps) {
  if (isLoading) {
    return <LoadingRows rows={3} label="Cargando dependencias" />;
  }

  const entries = Object.entries(dependencies);
  if (entries.length === 0) {
    return <EmptyState title="El gateway no informó dependencias." />;
  }
  const hasOptionalDegradation = entries.some(
    ([, dependency]) => dependency.required === false && dependency.status === "degraded",
  );

  return (
    <section className="flex flex-col gap-3">
      {hasOptionalDegradation ? (
        <Alert variant="warning">
          <AlertDescription>Una dependencia opcional degradada no bloquea el gateway.</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid border-t border-l border-line md:grid-cols-2 xl:grid-cols-3">
        {entries.map(([name, dependency]) => {
          const metrics = buildMetadata(dependency);
          const tone =
            dependency.status === "ready" ? "bg-ok" : dependency.status === "degraded" ? "bg-warn" : "bg-danger";

          return (
            <article key={name} className="flex flex-col gap-2 border-r border-b border-line px-4 py-3">
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="m-0 font-mono text-[13px] font-medium text-ink">{name}</h3>
                <span className="inline-flex items-center gap-1.5 font-label text-[13px] font-semibold text-ink">
                  <span aria-hidden className={`size-2 rounded-full ${tone}`} />
                  {formatHealthLabel(dependency.status)}
                </span>
              </div>
              <p className="m-0 text-sm text-ink-2">{dependency.detail}</p>
              {metrics.length > 0 ? (
                <Readout
                  items={metrics.map(([label, value]) => ({
                    label,
                    value: (
                      <span className="text-sm font-medium">
                        {typeof value === "string" ? formatHealthLabel(value) : formatHealthValue(value)}
                      </span>
                    ),
                  }))}
                />
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
