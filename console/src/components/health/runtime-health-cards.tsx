import { RuntimeHealthDependency } from "@/lib/admin-api";
import { formatTimestamp } from "@/components/observability/format";
import {
  dependencyClassLabel,
  healthReasonLabel,
  lastRunStatusLabel,
  runtimeStatusLabel,
  servingEffectLabel,
} from "@/components/system/labels";
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

/** One reading of a card; `read` words a raw value (a code, a moment) as the operator reads it, keeping the raw value as the title. */
type MetadataRow = { label: string; value: unknown; read?: (raw: string) => string };

function buildMetadata(dependency: RuntimeHealthDependency): MetadataRow[] {
  const metadata: MetadataRow[] = [
    { label: "Clase", value: dependency.dependency_class, read: dependencyClassLabel },
    { label: "Ciclo de vida", value: dependency.lifecycle_state, read: runtimeStatusLabel },
    { label: "Efecto", value: dependency.serving_effect, read: servingEffectLabel },
    { label: "Código", value: dependency.reason_code, read: healthReasonLabel },
    { label: "Activada", value: dependency.enabled },
    { label: "Recuperándose", value: dependency.recovering },
    { label: "Última falla", value: dependency.last_failure_at, read: formatTimestamp },
    { label: "Última recuperación", value: dependency.last_recovery_at, read: formatTimestamp },
    { label: "Último estado", value: dependency.last_status, read: lastRunStatusLabel },
    { label: "Última corrida", value: dependency.last_run_at, read: formatTimestamp },
    { label: "Último intento", value: dependency.last_attempted_run_at, read: formatTimestamp },
    { label: "Filas borradas", value: dependency.last_deleted_count },
    { label: "Filas elegibles", value: dependency.last_eligible_count },
    { label: "Último corte", value: dependency.last_cutoff, read: formatTimestamp },
    { label: "Último error", value: dependency.last_error },
  ];

  return metadata.filter(({ value }) => value !== undefined);
}

function MetadataValue({ row }: { row: MetadataRow }) {
  if (typeof row.value === "string") {
    return (
      <span className="text-sm font-medium" title={row.read ? row.value : undefined}>
        {row.read ? row.read(row.value) : row.value}
      </span>
    );
  }
  return <span className="text-sm font-medium">{formatHealthValue(row.value)}</span>;
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
                <span
                  className="inline-flex items-center gap-1.5 font-label text-[13px] font-semibold text-ink"
                  title={dependency.status}
                >
                  <span aria-hidden className={`size-2 rounded-full ${tone}`} />
                  {runtimeStatusLabel(dependency.status)}
                </span>
              </div>
              <p className="m-0 text-sm text-ink-2">{dependency.detail}</p>
              {metrics.length > 0 ? (
                <Readout items={metrics.map((row) => ({ label: row.label, value: <MetadataValue row={row} /> }))} />
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
