import type { ReactNode } from "react";

import { cn } from "cn";

export type ReadoutItem = { label: string; value: ReactNode; emphasis?: boolean; detail?: ReactNode };

/** Instrument-style readings: label left, value right, 1px rules between rows. */
export function Readout({ items, className }: { items: ReadoutItem[]; className?: string }) {
  return (
    <dl className={cn("m-0 border-t border-line", className)}>
      {items.map((item) => (
        <div key={item.label} role="group" aria-label={item.label} className="border-b border-line py-2">
          <div className="flex items-baseline justify-between gap-4">
            <dt className="text-sm text-ink-2">{item.label}</dt>
            <dd
              className={cn(
                "m-0 text-right font-semibold text-ink",
                item.emphasis ? "text-[22px] leading-tight" : "text-base",
              )}
            >
              {item.value}
            </dd>
          </div>
          {item.detail ? <div className="mt-0.5 text-right text-[13px] text-ink-3">{item.detail}</div> : null}
        </div>
      ))}
    </dl>
  );
}
