import { screen } from "@testing-library/react";
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

describe("ledger-table", () => {
  it("renders the ledger columns and selects a row on click", async () => {
    const onSelectRow = vi.fn();
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-001" onSelectRow={onSelectRow} isLoading={false} />);

    for (const name of ["Hora", "Pedido", "Nivel", "Modelo", "Tokens", "USD", "Latencia", "Estado"]) {
      expect(screen.getByRole("columnheader", { name })).toBeInTheDocument();
    }
    await userEvent.click(screen.getByRole("row", { name: /req-002/ }));
    expect(onSelectRow).toHaveBeenCalledWith("req-002");
  });

  it("marks the selected row and derives the tier from the route signals", () => {
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-002" onSelectRow={vi.fn()} isLoading={false} />);

    const selected = screen.getByRole("row", { selected: true });
    expect(selected).toHaveTextContent("req-002");
    expect(selected).toHaveTextContent("economy");
    expect(screen.getByRole("row", { name: /req-003/ })).toHaveTextContent("caché");
    expect(screen.getByRole("row", { name: /req-002/ })).toHaveTextContent("0.0018");
  });

  it("moves the selection with the arrow keys and selects with Enter", async () => {
    const user = userEvent.setup();
    const onSelectRow = vi.fn();
    renderWithProviders(<LedgerTable rows={rows} selectedRequestId="req-001" onSelectRow={onSelectRow} isLoading={false} />);

    screen.getByRole("row", { name: /req-001/ }).focus();
    await user.keyboard("{ArrowDown}");
    expect(onSelectRow).toHaveBeenLastCalledWith("req-002");
    expect(screen.getByRole("row", { name: /req-002/ })).toHaveFocus();
    await user.keyboard("{ArrowDown}{Enter}");
    expect(onSelectRow).toHaveBeenLastCalledWith("req-003");
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
