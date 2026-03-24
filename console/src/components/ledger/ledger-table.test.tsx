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

    await user.click(screen.getByRole("row", { name: /req-001/i }));
    expect(onSelectRow).toHaveBeenCalledWith("req-001");
  });

  it("exposes request identity in the row so embeddings entries stay discoverable", () => {
    renderWithProviders(
      <LedgerTable
        rows={[baseRow]}
        selectedRequestId={"req-001"}
        onSelectRow={() => {}}
        isLoading={false}
      />,
    );

    expect(screen.getByText("Request ID")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /req-001/i })).toHaveClass("bg-sky-50");
    expect(screen.getByText("embeddings")).toBeInTheDocument();
    expect(screen.queryByText(/text to embed/i)).not.toBeInTheDocument();
  });
});
