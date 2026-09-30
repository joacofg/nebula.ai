import { cn } from "cn";

const TIERS: Record<string, { label: string; swatch: string }> = {
  local: { label: "local", swatch: "bg-tier-local" },
  economy: { label: "economy", swatch: "bg-tier-economy" },
  frontier: { label: "frontier", swatch: "bg-tier-frontier" },
  cache: { label: "caché", swatch: "bg-tier-cache" },
  denied: { label: "denegado", swatch: "bg-danger" },
};

export function tierLabel(tier: string) {
  return TIERS[tier]?.label ?? tier;
}

export function TierBadge({ tier, className }: { tier: string; className?: string }) {
  const known = TIERS[tier];
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap font-label text-[13px] font-medium", className)}>
      <span aria-hidden className={cn("size-2.5 shrink-0", known?.swatch ?? "border border-ink-3")} />
      {known?.label ?? tier}
    </span>
  );
}
