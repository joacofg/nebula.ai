import type { CacheControlSummary } from "@/lib/admin-api";

import { Readout } from "@/components/system/readout";

const LEVEL: Record<string, string> = { info: "info", notice: "aviso", warning: "alerta" };

export function CacheSummary({ cache }: { cache: CacheControlSummary }) {
  return (
    <div className="grid max-w-5xl gap-8 lg:grid-cols-2">
      <div className="flex flex-col gap-2">
        <Readout
          items={[
            { label: "Tasa de aciertos estimada", value: `${Math.round(cache.estimated_hit_rate * 100)} %`, emphasis: true },
            { label: "Premium evitado", value: `USD ${cache.avoided_premium_cost_usd.toFixed(2)}`, emphasis: true },
            { label: "Caché activada", value: cache.enabled ? "sí" : "no" },
            { label: "Estado en runtime", value: cache.runtime_status },
            { label: "Umbral de similitud", value: cache.similarity_threshold.toFixed(2) },
            { label: "Antigüedad máxima", value: `${cache.max_entry_age_hours} h` },
          ]}
        />
        <p className="m-0 text-[13px] text-ink-3">{cache.runtime_detail}</p>
      </div>
      <div className="flex flex-col gap-4">
        {cache.insights.length === 0 ? (
          <p className="m-0 text-sm text-ink-3">Sin observaciones del caché en esta ventana.</p>
        ) : (
          cache.insights.map((insight) => (
            <article key={insight.code} className="flex flex-col gap-1.5 border-t border-line pt-3">
              <div className="flex items-baseline gap-3">
                <h3 className="m-0 text-base font-semibold text-ink">{insight.title}</h3>
                <span className="font-label text-[13px] font-medium text-ink-3">{LEVEL[insight.level] ?? insight.level}</span>
              </div>
              <p className="m-0 text-sm text-ink-2">{insight.summary}</p>
              {insight.evidence.length ? (
                <Readout items={insight.evidence.map((e) => ({ label: e.label, value: <span className="text-sm">{e.value}</span> }))} />
              ) : null}
            </article>
          ))
        )}
      </div>
    </div>
  );
}
