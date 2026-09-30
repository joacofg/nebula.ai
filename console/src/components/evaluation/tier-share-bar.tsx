import { TIER_COLORS, formatShare } from "@/components/evaluation/format";
import { TIERS, type TierShare } from "@/lib/router-replay";

export function TierShareBar({ share }: { share: TierShare }) {
  const visible = TIERS.filter((t) => share[t] > 0);
  return (
    <div className="space-y-3">
      {/* A 2px surface gap between segments; each segment keeps its own round ends. */}
      <div className="flex h-3 w-full gap-[2px] overflow-hidden rounded-sm bg-slate-100" aria-hidden>
        {visible.map((t) => (
          <div
            key={t}
            className="h-full rounded-[3px]"
            style={{ width: `${share[t] * 100}%`, backgroundColor: TIER_COLORS[t] }}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-700" aria-label="Reparto por nivel">
        {TIERS.map((t) => (
          <li key={t} className="inline-flex items-center gap-2">
            <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-xs" style={{ backgroundColor: TIER_COLORS[t] }} />
            <span className="font-mono text-xs">{t}</span>
            <span className="font-semibold tabular-nums text-slate-950">{formatShare(share[t])}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
