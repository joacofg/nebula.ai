import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LedgerTable } from "@/components/ledger/ledger-table";
import type { UsageLedgerRecord } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const baseRow: UsageLedgerRecord = {
  request_id: "req-001",
  tenant_id: "default",
  requested_model: "text-embedding-3-small",
  final_route_target: "embeddings",
  final_provider: "openai-compatible",
  fallback_used: false,
  cache_hit: false,
  response_model: "text-embedding-3-small",
  prompt_tokens: 19,
  completion_tokens: 0,
  total_tokens: 19,
  estimated_cost: 0.016,
  latency_ms: 180,
  timestamp: "2026-03-16T22:00:00Z",
  terminal_status: "completed",
  route_reason: "embeddings_request",
  policy_outcome: "allowed",
  route_signals: null,
  message_type: "chat",
  evidence_retention_window: "30d",
  evidence_expires_at: null,
  metadata_minimization_level: "standard",
  metadata_fields_suppressed: [],
  governance_source: "tenant_policy",
};

const rows: UsageLedgerRecord[] = [
  baseRow,
  {
    ...baseRow,
    request_id: "req-002",
    final_route_target: "premium",
    response_model: "anthropic/claude-haiku-4.5-with-a-very-long-model-identifier",
    route_reason: "learned_router",
    route_signals: { tier: "economy", learned_router: "v1" },
    estimated_cost: 0.0018,
  },
  { ...baseRow, request_id: "req-003", final_route_target: "cache", cache_hit: true, estimated_cost: 0 },
];

function bodyRows() {
  return screen.getAllByRole("row").filter((row) => row.closest("tbody"));
}

describe("ledger-table", () => {
  it("renders the ledger columns and selects a row on click", async () => {
    const onSelectRow = vi.fn();
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-001" onSelectRow={onSelectRow} isLoading={false} />);

    expect(screen.getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      "Fecha",
      "Pedido",
      "Nivel",
      "Modelo",
      "Costo",
      "Latencia",
      "Estado",
    ]);
    await userEvent.click(screen.getByRole("row", { name: /req-002/ }));
    expect(onSelectRow).toHaveBeenCalledWith("req-002");
  });

  it("marks the selected row as current and derives the tier from the route signals", () => {
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-002" onSelectRow={vi.fn()} isLoading={false} />);

    const selected = screen.getByRole("row", { current: true });
    expect(selected).toHaveTextContent("req-002");
    expect(selected).toHaveTextContent("economy");
    expect(screen.getByRole("row", { name: /req-003/ })).toHaveTextContent("caché");
    expect(screen.getByRole("row", { name: /req-002/ })).toHaveTextContent("USD 0.0018");
    // A row is not a selectable widget here: nothing announces "selected".
    expect(selected).toHaveAttribute("aria-current", "true");
    for (const row of bodyRows()) {
      expect(row).not.toHaveAttribute("aria-selected");
    }
    expect(screen.getAllByRole("row", { current: true })).toHaveLength(1);
  });

  it("titles the Estado cell with the Spanish label, never the gateway's code", () => {
    const statuses = [
      ["fallback_completed", "completado con fallback"],
      ["policy_denied", "denegado por política"],
      ["provider_error", "error del proveedor"],
      ["rate_limited", "límite de pedidos"],
      ["client_disconnected", "cortado por el cliente"],
    ] as const;
    const statusRows = statuses.map(([status], index) => ({
      ...baseRow,
      request_id: `req-status-${index}`,
      terminal_status: status,
    }));
    renderWithProviders(<LedgerTable rows={statusRows} selectedRequestId={null} onSelectRow={vi.fn()} isLoading={false} />);

    statuses.forEach(([status, label], index) => {
      const cells = within(screen.getByRole("row", { name: new RegExp(`req-status-${index}`) })).getAllByRole("cell");
      const estado = cells[cells.length - 1];
      expect(estado).toHaveTextContent(label);
      expect(estado).toHaveAttribute("title", label);
      expect(estado).not.toHaveAttribute("title", status);
    });
  });

  it("shows the date and the time on the viewer's clock", () => {
    const stamped = [
      { ...baseRow, request_id: "req-utc", timestamp: new Date(2026, 9, 22, 14, 5, 3).toISOString() },
      // SQLite returns timestamps without a zone; they are UTC, so both spellings read the same.
      { ...baseRow, request_id: "req-naive", timestamp: "2026-10-22T14:05:03.123456" },
      { ...baseRow, request_id: "req-zoned", timestamp: "2026-10-22T14:05:03Z" },
    ];
    renderWithProviders(<LedgerTable rows={stamped} selectedRequestId={null} onSelectRow={vi.fn()} isLoading={false} />);

    expect(screen.getByRole("row", { name: /req-utc/ })).toHaveTextContent("22/10 14:05:03");
    const zoned = within(screen.getByRole("row", { name: /req-zoned/ })).getAllByRole("cell")[0].textContent;
    expect(within(screen.getByRole("row", { name: /req-naive/ })).getAllByRole("cell")[0]).toHaveTextContent(zoned ?? "");
    expect(zoned).toMatch(/^\d{2}\/\d{2} \d{2}:\d{2}:\d{2}$/);
  });

  it("keeps a single row in the tab order, on the selected one", () => {
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-002" onSelectRow={vi.fn()} isLoading={false} />);

    expect(bodyRows().filter((row) => row.tabIndex === 0)).toEqual([screen.getByRole("row", { name: /req-002/ })]);
  });

  it("starts the tab order on the first row when none is selected, and on the first when the selection left the page", () => {
    const { rerender } = renderWithProviders(
      <LedgerTable rows={rows} selectedRequestId={null} onSelectRow={vi.fn()} isLoading={false} />,
    );
    expect(bodyRows().map((row) => row.tabIndex)).toEqual([0, -1, -1]);

    rerender(<LedgerTable rows={rows} selectedRequestId="req-gone" onSelectRow={vi.fn()} isLoading={false} />);
    expect(bodyRows().map((row) => row.tabIndex)).toEqual([0, -1, -1]);
  });

  it("is one stop for Tab: it enters on the active row and leaves on the next press", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <>
        <LedgerTable rows={rows} selectedRequestId="req-002" onSelectRow={vi.fn()} isLoading={false} />
        <button type="button">Después</button>
      </>,
    );

    await user.tab();
    expect(screen.getByRole("row", { name: /req-002/ })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("button", { name: "Después" })).toHaveFocus();
    await user.tab({ shift: true });
    expect(screen.getByRole("row", { name: /req-002/ })).toHaveFocus();
  });

  it("moves focus with the arrow keys, takes the tab stop along, and opens with Enter", async () => {
    const user = userEvent.setup();
    const onSelectRow = vi.fn();
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-001" onSelectRow={onSelectRow} isLoading={false} />);

    await user.tab();
    expect(screen.getByRole("row", { name: /req-001/ })).toHaveFocus();
    await user.keyboard("{ArrowDown}");
    expect(screen.getByRole("row", { name: /req-002/ })).toHaveFocus();
    // Moving is not opening: the detail changes only on Enter.
    expect(onSelectRow).not.toHaveBeenCalled();
    expect(bodyRows().map((row) => row.tabIndex)).toEqual([-1, 0, -1]);

    await user.keyboard("{ArrowDown}");
    expect(screen.getByRole("row", { name: /req-003/ })).toHaveFocus();
    await user.keyboard("{ArrowUp}{ArrowUp}");
    expect(screen.getByRole("row", { name: /req-001/ })).toHaveFocus();

    await user.keyboard("{ArrowDown}{Enter}");
    expect(onSelectRow).toHaveBeenCalledTimes(1);
    expect(onSelectRow).toHaveBeenLastCalledWith("req-002");
  });

  it("stops at the first and last rows", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId={null} onSelectRow={vi.fn()} isLoading={false} />);

    await user.tab();
    expect(screen.getByRole("row", { name: /req-001/ })).toHaveFocus();
    await user.keyboard("{ArrowUp}");
    expect(screen.getByRole("row", { name: /req-001/ })).toHaveFocus();
    await user.keyboard("{ArrowDown}{ArrowDown}{ArrowDown}");
    expect(screen.getByRole("row", { name: /req-003/ })).toHaveFocus();
  });

  it("keeps the tab stop on the clicked row", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-001" onSelectRow={vi.fn()} isLoading={false} />);

    await user.click(screen.getByRole("row", { name: /req-003/ }));
    expect(bodyRows().map((row) => row.tabIndex)).toEqual([-1, -1, 0]);
  });

  it("keeps exactly one tab stop when the row that had focus leaves the list", async () => {
    const user = userEvent.setup();
    const table = (shown: UsageLedgerRecord[], selected: string | null) => (
      <LedgerTable rows={shown} selectedRequestId={selected} onSelectRow={vi.fn()} isLoading={false} />
    );
    const { rerender } = renderWithProviders(table(rows, "req-001"));
    await user.tab();
    await user.keyboard("{ArrowDown}{ArrowDown}");
    expect(screen.getByRole("row", { name: /req-003/ })).toHaveFocus();

    // The focused row is gone: the stop falls back to the selected row.
    rerender(table(rows.slice(0, 2), "req-001"));
    expect(bodyRows().map((row) => row.tabIndex)).toEqual([0, -1]);

    // The selected row is gone too: it falls back to the first one.
    rerender(table(rows.slice(1, 2), "req-001"));
    expect(bodyRows().map((row) => row.tabIndex)).toEqual([0]);
  });

  it("keeps long values on one line with the full text in the title", () => {
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId={null} onSelectRow={vi.fn()} isLoading={false} />);
    const cell = screen.getByText("anthropic/claude-haiku-4.5-with-a-very-long-model-identifier");
    expect(cell).toHaveAttribute("title", "anthropic/claude-haiku-4.5-with-a-very-long-model-identifier");
    expect(cell.className).toContain("truncate");
  });

  it("offers the playground when the range has no requests", () => {
    renderWithProviders(<LedgerTable rows={[]} selectedRequestId={null} onSelectRow={vi.fn()} isLoading={false} />);
    expect(screen.getByText("No hay pedidos en este rango.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir Playground" })).toHaveAttribute("href", "/playground");
  });

  it("announces loading", () => {
    renderWithProviders(<LedgerTable rows={[]} selectedRequestId={null} onSelectRow={vi.fn()} isLoading />);
    expect(screen.getByRole("status", { name: "Cargando pedidos" })).toBeInTheDocument();
  });
});
