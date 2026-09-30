import type { RecommendationBundle } from "@/lib/admin-api";

import { plural } from "@/components/system/labels";
import { Readout } from "@/components/system/readout";
import { EmptyState } from "@/components/system/state";

const CATEGORY: Record<string, string> = { policy: "política", cache: "caché", info: "info" };

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
        bundle.recommendations.map((item) => (
          <article key={item.code} className="flex flex-col gap-2 border-t border-line pt-3">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h3 className="m-0 text-base font-semibold text-ink">{item.title}</h3>
              <span className="font-label text-[13px] font-medium text-ink-3">
                {CATEGORY[item.category] ?? item.category} · prioridad {item.priority}
              </span>
              <span className="ml-auto font-mono text-[12px] text-ink-3">{item.code}</span>
            </div>
            <p className="m-0 text-sm text-ink-2">{item.summary}</p>
            <p className="m-0 text-sm text-ink">
              <span className="font-semibold">Acción recomendada: </span>
              {item.recommended_action}
            </p>
            {item.evidence.length ? (
              <Readout items={item.evidence.map((e) => ({ label: e.label, value: <span className="text-sm">{e.value}</span> }))} />
            ) : null}
          </article>
        ))
      )}
    </div>
  );
}
