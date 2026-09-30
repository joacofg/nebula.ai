import type { CalibrationEvidenceSummary } from "@/lib/admin-api";

import { formatReasonCounts, formatTimestamp } from "@/components/observability/format";
import { Readout, type ReadoutItem } from "@/components/system/readout";

type Explanation = { badge: string; summary: string; items: ReadoutItem[] };

export function explainCalibration(summary: CalibrationEvidenceSummary): Explanation {
  const eligible = summary.eligible_request_count ?? 0;
  const threshold = summary.thin_request_threshold ?? 0;
  const gated = summary.gated_request_count ?? 0;
  const degraded = summary.degraded_request_count ?? 0;
  const excluded = summary.excluded_request_count ?? 0;

  const items: ReadoutItem[] = [
    { label: "Filas elegibles", value: `${eligible} de ${threshold} necesarias` },
    {
      label: "Última fila elegible",
      value: summary.latest_eligible_request_at ? formatTimestamp(summary.latest_eligible_request_at) : "Sin filas elegibles",
    },
  ];
  if (gated > 0) {
    items.push({ label: "Filas con rollout desactivado", value: `${gated} (${formatReasonCounts(summary.gated_reasons)})` });
  }
  if (degraded > 0) {
    items.push({ label: "Filas degradadas", value: `${degraded} (${formatReasonCounts(summary.degraded_reasons)})` });
  }
  if (excluded > 0) {
    items.push({ label: "Filas excluidas", value: `${excluded} (${formatReasonCounts(summary.excluded_reasons)})` });
  }

  if (summary.state === "sufficient") {
    return { badge: "suficiente", summary: "La evidencia del tenant alcanza para el ruteo calibrado.", items };
  }
  if (summary.state === "stale") {
    items.push({ label: "Umbral de vencimiento", value: `${summary.staleness_threshold_hours} h` });
    return { badge: "vencida", summary: "La evidencia del tenant alcanzaba, pero la ventana ya venció.", items };
  }
  if (summary.state === "degraded") {
    return { badge: "degradada", summary: "La evidencia reciente está degradada: faltan señales en parte del tráfico.", items };
  }
  if (gated > 0 && eligible === 0) {
    return { badge: "rollout desactivado", summary: "Hay tráfico, pero el ruteo calibrado sigue desactivado por el operador.", items };
  }
  return { badge: "escasa", summary: "La evidencia del tenant todavía es escasa para el ruteo calibrado.", items };
}

/** Tenant-level evidence for the heuristic router's calibration (v0 baseline). */
export function CalibrationSummary({ summary }: { summary: CalibrationEvidenceSummary }) {
  const explanation = explainCalibration(summary);
  return (
    <div className="flex max-w-2xl flex-col gap-3">
      <div className="flex items-baseline gap-3">
        <span className="border border-line-strong px-2 py-0.5 font-label text-[13px] font-semibold text-ink">
          {explanation.badge}
        </span>
        <p className="m-0 text-[15px] text-ink">{explanation.summary}</p>
      </div>
      <Readout items={explanation.items} />
    </div>
  );
}
