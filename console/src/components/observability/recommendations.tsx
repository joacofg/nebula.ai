import type { RecommendationBundle } from "@/lib/admin-api";

import { plural } from "@/components/system/labels";
import { Readout } from "@/components/system/readout";
import { EmptyState } from "@/components/system/state";

const CATEGORY: Record<string, string> = { policy: "política", cache: "caché", info: "info" };

type Copy = { title: string; summary: string; action: string };

/** The gateway's API stays in English; the console reads its known recommendation codes in Spanish. */
const COPY: Record<string, Copy> = {
  restore_semantic_cache_runtime: {
    title: "Restaurar la caché semántica",
    summary: "La caché no está disponible y sus sugerencias quedan limitadas.",
    action: "Recuperar la dependencia de la caché antes de ajustar umbrales.",
  },
  tune_semantic_cache_threshold: {
    title: "Revisar el ajuste de la caché semántica",
    summary: "La caché está activa, pero la tasa de aciertos reciente es baja.",
    action: "Revisar el umbral de similitud y la antigüedad máxima de las entradas.",
  },
  review_premium_routing_pressure: {
    title: "Revisar la presión sobre premium",
    summary: "Buena parte del tráfico reciente fue a premium, con costo medible.",
    action: "Revisar el ruteo por defecto y los límites de presupuesto.",
  },
  inspect_policy_denials: {
    title: "Revisar las denegaciones recientes",
    summary: "El ledger tiene pedidos denegados por política o presupuesto.",
    action: "Contrastar los modelos premium permitidos y el límite por pedido con lo esperado.",
  },
  no_action_needed: {
    title: "Sin recomendaciones inmediatas",
    summary: "El ledger y la caché no muestran acciones pendientes.",
    action: "Seguir monitoreando la política y la caché.",
  },
};

const EVIDENCE: Record<string, string> = {
  cache_hit_rate: "Tasa de aciertos",
  similarity_threshold: "Umbral de similitud",
  max_entry_age_hours: "Antigüedad máxima (h)",
  premium_share: "Proporción premium",
  premium_cost_usd: "Costo premium (USD)",
  routing_mode_default: "Modo de ruteo",
  policy_denials: "Denegaciones",
  max_premium_cost_per_request: "Costo premium máximo por pedido",
  window_requests: "Pedidos en la ventana",
  last_request_at: "Último pedido",
  cache_runtime_status: "Estado de la caché",
  cache_runtime_detail: "Detalle",
};

export function Recommendations({ bundle }: { bundle: RecommendationBundle }) {
  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <p className="m-0 font-label text-[13px] font-medium text-ink-3">
        {plural(bundle.recommendations.length, "recomendación", "recomendaciones")} · ventana de{" "}
        {plural(bundle.window_requests_evaluated, "pedido", "pedidos")}
      </p>
      {bundle.recommendations.length === 0 ? (
        <EmptyState title="Sin recomendaciones para esta ventana." />
      ) : (
        bundle.recommendations.map((item) => {
          const copy = COPY[item.code];
          return (
            <article key={item.code} className="flex flex-col gap-2 border-t border-line pt-3">
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <h3 className="m-0 text-base font-semibold text-ink">{copy?.title ?? item.title}</h3>
                <span className="font-label text-[13px] font-medium text-ink-3">
                  {CATEGORY[item.category] ?? item.category} · prioridad {item.priority}
                </span>
                <span className="ml-auto font-mono text-[12px] text-ink-3">{item.code}</span>
              </div>
              <p className="m-0 text-sm text-ink-2">{copy?.summary ?? item.summary}</p>
              <p className="m-0 text-sm text-ink">
                <span className="font-semibold">Acción recomendada: </span>
                {copy?.action ?? item.recommended_action}
              </p>
              {item.evidence.length ? (
                <Readout
                  items={item.evidence.map((e) => ({
                    label: EVIDENCE[e.label] ?? e.label,
                    value: <span className="text-sm">{e.value}</span>,
                  }))}
                />
              ) : null}
            </article>
          );
        })
      )}
    </div>
  );
}
