import { TIER_COLORS, formatShare } from "@/components/evaluation/format";
import { TIERS, type Tier, type TierShare } from "@/lib/router-replay";

type TierShareBarProps = {
  share: TierShare;
  /** The model each tier ran; a tier without one shows its name only. */
  models?: Partial<Record<Tier, string>>;
};

export function TierShareBar({ share, models = {} }: TierShareBarProps) {
  const visible = TIERS.filter((t) => share[t] > 0);
  return (
    <div className="flex flex-col gap-2">
      {/* 2px surface gap between segments; a present tier never shrinks below 2px. */}
      <div className="flex h-3.5 w-full gap-[2px]" aria-hidden>
        {visible.map((t) => (
          <div
            key={t}
            className="h-full min-w-[2px] motion-safe:transition-[flex-grow] motion-safe:duration-250 motion-safe:ease-out-expo"
            style={{ flex: `${share[t]} 1 0`, backgroundColor: TIER_COLORS[t] }}
          />
        ))}
      </div>
      <ul className="m-0 flex list-none flex-col gap-1 p-0 font-label text-[13px] font-medium text-ink-2" aria-label="Reparto por nivel">
        {TIERS.map((t) => (
          <li key={t} className="flex items-center gap-2">
            <span aria-hidden className="inline-block size-2.5 shrink-0" style={{ backgroundColor: TIER_COLORS[t] }} />
            <span className="w-16 shrink-0">{t}</span>
            <span className="min-w-0 flex-1 truncate font-mono text-xs font-normal text-ink-3" title={models[t]}>
              {models[t]}
            </span>
            <span className="font-sans text-sm font-semibold text-ink">{formatShare(share[t])}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
