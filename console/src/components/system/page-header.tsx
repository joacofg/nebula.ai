import type { ReactNode } from "react";

import { cn } from "cn";

export type PageHeaderCell = { label: string; value: ReactNode };

type PageHeaderProps = {
  title: string;
  cells?: PageHeaderCell[];
  actions?: ReactNode;
  className?: string;
};

/** The drawing title block: page title plus context cells separated by 1px rules. */
export function PageHeader({ title, cells = [], actions, className }: PageHeaderProps) {
  return (
    <header className={cn("flex min-h-20 flex-wrap items-stretch border-b border-line-strong bg-surface", className)}>
      <div className="flex min-w-[240px] flex-[1.6] items-center px-6 py-3">
        <h1 className="m-0 text-[26px] font-semibold leading-tight tracking-[-0.015em] text-ink">{title}</h1>
      </div>
      {cells.map((cell) => (
        <div key={cell.label} className="flex min-w-[140px] flex-1 flex-col justify-center border-l border-line px-5 py-3">
          <span className="font-label text-[13px] font-medium text-ink-3">{cell.label}</span>
          <span className="font-semibold text-ink">{cell.value}</span>
        </div>
      ))}
      {actions ? <div className="flex items-center gap-2 border-l border-line px-5 py-3">{actions}</div> : null}
    </header>
  );
}
