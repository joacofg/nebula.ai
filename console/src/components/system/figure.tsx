import type { ReactNode } from "react";

import { cn } from "cn";

type FigureProps = {
  caption: ReactNode;
  children: ReactNode;
  className?: string;
};

/**
 * A figure with its caption. The caption carries no figure number: the thesis numbers each
 * capture in its own document, so a number inside the app would end up in the wrong place.
 */
export function Figure({ caption, children, className }: FigureProps) {
  return (
    <figure className={cn("m-0 flex flex-col gap-2", className)}>
      {children}
      <figcaption className="text-sm text-ink-2">{caption}</figcaption>
    </figure>
  );
}
