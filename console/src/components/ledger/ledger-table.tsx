"use client";

import type { KeyboardEvent } from "react";

import { useState } from "react";

import Link from "next/link";
import { cn } from "cn";

import { statusLabel } from "@/components/system/labels";
import { TierBadge } from "@/components/system/tier-badge";
import { EmptyState, LoadingRows } from "@/components/system/state";
import type { UsageLedgerRecord } from "@/lib/admin-api";
import { formatDateTime, formatUsd } from "@/lib/format";

type LedgerTableProps = {
  rows: UsageLedgerRecord[];
  selectedRequestId: string | null;
  onSelectRow: (requestId: string) => void;
  isLoading: boolean;
};

/**
 * The level a row was served at: the learned router's tier for premium traffic, the route otherwise.
 * The ledger's `tier` filter applies this same rule (`list_usage_records` in governance_store.py).
 */
export function rowTier(row: UsageLedgerRecord) {
  const signals = row.route_signals as Record<string, unknown> | null;
  if (row.final_route_target === "premium" && typeof signals?.tier === "string") {
    return signals.tier;
  }
  return row.final_route_target;
}

function formatCost(value: number | null) {
  return value === null ? "—" : formatUsd(value, 4);
}

export function formatLatency(value: number | null) {
  if (value === null) {
    return "—";
  }
  return value >= 1000 ? `${(value / 1000).toFixed(1)} s` : `${Math.round(value)} ms`;
}

const HEAD = "px-3 py-2 text-left font-label text-[13px] font-semibold text-ink-2";

export function LedgerTable({ rows, selectedRequestId, onSelectRow, isLoading }: LedgerTableProps) {
  // The row that last had focus. The table is one stop for Tab (roving tabindex): up to 500 rows
  // would otherwise be 500 stops, and the arrow keys move between them.
  const [focusedRequestId, setFocusedRequestId] = useState<string | null>(null);

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

  // Tab lands on the row that has focus, else the selected one, else the first.
  const tabStopRequestId =
    [focusedRequestId, selectedRequestId].find((id) => id !== null && rows.some((row) => row.request_id === id)) ??
    rows[0].request_id;

  /** The arrows move focus only; the detail changes on Enter, so browsing does not reload it. */
  function onRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, requestId: string) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const sibling =
        event.key === "ArrowDown" ? event.currentTarget.nextElementSibling : event.currentTarget.previousElementSibling;
      (sibling as HTMLElement | null)?.focus();
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelectRow(requestId);
    }
  }

  return (
    <div className="max-h-[620px] overflow-auto">
      {/* Fixed columns sized to their content ("23/10 14:05:03", "USD 0.0000", "completado"), so at
          1440 px the table fits its 776 px cell and Modelo keeps room for "openai/gpt-4.1". */}
      <table className="w-full min-w-[760px] table-fixed border-collapse text-sm" aria-label="Ledger de pedidos">
        <colgroup>
          <col className="w-[126px]" />
          <col className="w-[88px]" />
          <col className="w-[96px]" />
          <col />
          <col className="w-[68px]" />
          <col className="w-[96px]" />
          <col className="w-[76px]" />
          <col className="w-[96px]" />
        </colgroup>
        <thead>
          <tr className="sticky top-0 z-10 border-b border-line-strong bg-surface shadow-[inset_0_-1px_0_var(--color-line-strong)]">
            <th scope="col" className={HEAD}>Fecha</th>
            <th scope="col" className={HEAD}>Pedido</th>
            <th scope="col" className={HEAD}>Nivel</th>
            <th scope="col" className={HEAD}>Modelo</th>
            <th scope="col" className={cn(HEAD, "text-right")}>Tokens</th>
            <th scope="col" className={cn(HEAD, "text-right")}>Costo</th>
            <th scope="col" className={cn(HEAD, "text-right")}>Latencia</th>
            <th scope="col" className={HEAD}>Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const selected = row.request_id === selectedRequestId;
            return (
              <tr
                key={row.request_id}
                tabIndex={row.request_id === tabStopRequestId ? 0 : -1}
                aria-current={selected ? "true" : undefined}
                aria-label={`Pedido ${row.request_id}`}
                onClick={() => onSelectRow(row.request_id)}
                onFocus={() => setFocusedRequestId(row.request_id)}
                onKeyDown={(event) => onRowKeyDown(event, row.request_id)}
                className={cn(
                  "cursor-pointer border-b border-line transition-colors duration-100 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-mark",
                  selected ? "bg-mark-soft shadow-[inset_0_1px_0_var(--color-mark-line),inset_0_-1px_0_var(--color-mark-line)]" : "hover:bg-canvas",
                )}
              >
                <td className="truncate px-3 py-2 font-mono text-[12px] text-ink-3">{formatDateTime(row.timestamp)}</td>
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
                <td className="whitespace-nowrap px-3 py-2 text-right font-medium">{formatCost(row.estimated_cost)}</td>
                <td className="px-3 py-2 text-right font-medium">{formatLatency(row.latency_ms)}</td>
                <td className="truncate px-3 py-2 font-label text-[13px] text-ink-2" title={row.terminal_status}>
                  {statusLabel(row.terminal_status)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
