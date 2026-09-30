import type { ReactNode } from "react";

import { cn } from "cn";

type FigureProps = {
  number: number;
  caption: ReactNode;
  children: ReactNode;
  className?: string;
};

export function Figure({ number, caption, children, className }: FigureProps) {
  return (
    <figure className={cn("m-0 flex flex-col gap-2", className)}>
      {children}
      <figcaption className="text-sm text-ink-2">
        <span className="font-semibold text-ink">{`Figura ${number}.`}</span> <span>{caption}</span>
      </figcaption>
    </figure>
  );
}
