import type { CacheControlSummary } from "@/lib/admin-api";

import { cacheEvidenceLabel, cacheInsightLabel, insightLevelLabel, runtimeStatusLabel } from "@/components/system/labels";
import { Readout } from "@/components/system/readout";
import { formatUsd } from "@/lib/format";

/** An evidence value the gateway wrote as text, read by what its row is; one it cannot read stays as written. */
function evidenceValue(label: string, value: string) {
  if (label === "runtime_status") {
    return runtimeStatusLabel(value);
  }
  if (label === "cache_enabled" && (value === "true" || value === "false")) {
    return value === "true" ? "sí" : "no";
  }
  if (label === "avoided_premium_cost_usd") {
    const amount = Number(value);
    return value.trim() !== "" && Number.isFinite(amount) ? formatUsd(amount, 4) : value;
  }
  return value;
}

export function CacheSummary({ cache }: { cache: CacheControlSummary }) {
  return (
    <div className="grid max-w-5xl gap-8 lg:grid-cols-2">
      <div className="flex flex-col gap-2">
        <Readout
          items={[
            { label: "Tasa de aciertos estimada", value: `${Math.round(cache.estimated_hit_rate * 100)} %`, emphasis: true },
            { label: "Premium evitado", value: formatUsd(cache.avoided_premium_cost_usd, 4), emphasis: true },
            { label: "Caché activado", value: cache.enabled ? "sí" : "no" },
            { label: "Estado en runtime", value: runtimeStatusLabel(cache.runtime_status) },
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
          cache.insights.map((insight) => {
            // An insight the console knows is worded in Spanish, and its evidence says the rest; the
            // gateway's English summary only stays for one it does not know.
            const title = cacheInsightLabel(insight.code);
            return (
              <article key={insight.code} className="flex flex-col gap-1.5 border-t border-line pt-3">
                <div className="flex items-baseline gap-3">
                  <h3 className="m-0 text-base font-semibold text-ink">{title ?? insight.title}</h3>
                  <span className="font-label text-[13px] font-medium text-ink-3">{insightLevelLabel(insight.level)}</span>
                </div>
                {title === null ? <p className="m-0 text-sm text-ink-2">{insight.summary}</p> : null}
                {insight.evidence.length ? (
                  <Readout
                    items={insight.evidence.map((e) => ({
                      label: cacheEvidenceLabel(e.label),
                      value: <span className="text-sm">{evidenceValue(e.label, e.value)}</span>,
                    }))}
                  />
                ) : null}
              </article>
            );
          })
        )}
      </div>
    </div>
  );
}
