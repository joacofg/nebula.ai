import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LedgerTable } from "@/components/ledger/ledger-table";
import { renderWithProviders } from "@/test/render";

const baseRow = {
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
} as const;

describe("ledger-table", () => {
  it("renders the usage-ledger columns and selects a row", async () => {
    const user = userEvent.setup();
    const onSelectRow = vi.fn();

    renderWithProviders(
      <LedgerTable
        rows={[baseRow]}
        selectedRequestId={null}
        onSelectRow={onSelectRow}
        isLoading={false}
      />,
    );

    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Latency")).toBeInTheDocument();
    expect(screen.getByText("Estimated cost")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /inspect request req-001/i }));
    expect(onSelectRow).toHaveBeenCalledWith("req-001");
  });

  it("marks the selected request as the current investigation without widening the table surface", () => {
    renderWithProviders(
      <LedgerTable
        rows={[baseRow]}
        selectedRequestId={"req-001"}
        onSelectRow={() => {}}
        isLoading={false}
      />,
    );

    expect(screen.getByText("Request ID")).toBeInTheDocument();
    expect(screen.getByRole("row", { selected: true })).toHaveClass("bg-sky-50/70");
    expect(screen.getByRole("button", { name: /current investigation: req-001/i })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Current investigation")).toBeInTheDocument();
    expect(screen.getByText("Primary request for the detail view below.")).toBeInTheDocument();
    expect(screen.getByText("embeddings")).toBeInTheDocument();
    expect(screen.queryByText(/text to embed/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics/i)).not.toBeInTheDocument();
  });

  it("keeps unselected rows discoverable as bounded request selectors", () => {
    renderWithProviders(
      <LedgerTable
        rows={[
          baseRow,
          {
            ...baseRow,
            request_id: "req-002",
            final_route_target: "premium",
          },
        ]}
        selectedRequestId={"req-001"}
        onSelectRow={() => {}}
        isLoading={false}
      />,
    );

    expect(screen.getByRole("button", { name: /current investigation: req-001/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /inspect request req-002/i })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("Select request")).toBeInTheDocument();
    expect(screen.getByText("Promote this request into the primary detail view.")).toBeInTheDocument();
  });
});
