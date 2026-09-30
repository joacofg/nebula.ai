"use client";

import type { KeyboardEvent } from "react";

import Link from "next/link";
import { cn } from "cn";

import { TierBadge } from "@/components/system/tier-badge";
import { EmptyState, LoadingRows } from "@/components/system/state";
import type { UsageLedgerRecord } from "@/lib/admin-api";

type LedgerTableProps = {
  rows: UsageLedgerRecord[];
  selectedRequestId: string | null;
  onSelectRow: (requestId: string) => void;
  isLoading: boolean;
};

/** The level a row was served at: the learned router's tier for premium traffic, the route otherwise. */
export function rowTier(row: UsageLedgerRecord) {
  const signals = row.route_signals as Record<string, unknown> | null;
  if (row.final_route_target === "premium" && typeof signals?.tier === "string") {
    return signals.tier;
  }
  return row.final_route_target;
}

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString("es-AR", { hour12: false });
}

function formatCost(value: number | null) {
  return value === null ? "—" : value.toFixed(4);
}

export function formatLatency(value: number | null) {
  if (value === null) {
    return "—";
  }
  return value >= 1000 ? `${(value / 1000).toFixed(1)} s` : `${Math.round(value)} ms`;
}

const HEAD = "px-3 py-2 text-left font-label text-[13px] font-semibold text-ink-2";

export function LedgerTable({ rows, selectedRequestId, onSelectRow, isLoading }: LedgerTableProps) {
  if (isLoading) {
    return <LoadingRows rows={8} label="Cargando pedidos" />;
  }

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No hay pedidos en este rango."
        action={
          <Link href="/playground" className="text-sm font-semibold text-ink underline underline-offset-4 hover:text-mark">
            Abrir Playground
          </Link>
        }
      />
    );
  }

  function onRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, index: number) {
    const move = event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0;
    if (move !== 0) {
      event.preventDefault();
      const next = rows[index + move];
      if (next) {
        onSelectRow(next.request_id);
        const sibling = move > 0 ? event.currentTarget.nextElementSibling : event.currentTarget.previousElementSibling;
        (sibling as HTMLElement | null)?.focus();
      }
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelectRow(rows[index].request_id);
    }
  }

  return (
    <div className="max-h-[620px] overflow-auto">
      <table className="w-full min-w-[760px] table-fixed border-collapse text-sm" aria-label="Ledger de pedidos">
        <colgroup>
          <col className="w-[84px]" />
          <col className="w-[104px]" />
          <col className="w-[104px]" />
          <col />
          <col className="w-[68px]" />
          <col className="w-[76px]" />
          <col className="w-[76px]" />
          <col className="w-[132px]" />
        </colgroup>
        <thead>
          <tr className="sticky top-0 z-10 border-b border-line-strong bg-surface shadow-[inset_0_-1px_0_var(--color-line-strong)]">
            <th scope="col" className={HEAD}>Hora</th>
            <th scope="col" className={HEAD}>Pedido</th>
            <th scope="col" className={HEAD}>Nivel</th>
            <th scope="col" className={HEAD}>Modelo</th>
            <th scope="col" className={cn(HEAD, "text-right")}>Tokens</th>
            <th scope="col" className={cn(HEAD, "text-right")}>USD</th>
            <th scope="col" className={cn(HEAD, "text-right")}>Latencia</th>
            <th scope="col" className={HEAD}>Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const selected = row.request_id === selectedRequestId;
            return (
              <tr
                key={row.request_id}
                tabIndex={0}
                aria-selected={selected}
                aria-label={`Pedido ${row.request_id}`}
                onClick={() => onSelectRow(row.request_id)}
                onKeyDown={(event) => onRowKeyDown(event, index)}
                className={cn(
                  "cursor-pointer border-b border-line transition-colors duration-100 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-mark",
                  selected ? "bg-mark-soft/70 shadow-[inset_2px_0_0_var(--color-mark)]" : "hover:bg-canvas",
                )}
              >
                <td className="truncate px-3 py-2 font-mono text-[12px] text-ink-3">{formatTime(row.timestamp)}</td>
                <td className="truncate px-3 py-2 font-mono text-[12px] text-ink-2" title={row.request_id}>
                  {row.request_id.slice(0, 8)}
                </td>
                <td className="px-3 py-2">
                  <TierBadge tier={rowTier(row)} />
                </td>
                <td className="px-3 py-2">
                  <span className="block truncate font-mono text-[12px] text-ink-2" title={row.response_model ?? ""}>
                    {row.response_model ?? "—"}
                  </span>
                </td>
                <td className="px-3 py-2 text-right font-medium">{row.total_tokens}</td>
                <td className="px-3 py-2 text-right font-medium">{formatCost(row.estimated_cost)}</td>
                <td className="px-3 py-2 text-right font-medium">{formatLatency(row.latency_ms)}</td>
                <td className="truncate px-3 py-2 font-label text-[13px] text-ink-2" title={row.terminal_status}>
                  {row.terminal_status}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
