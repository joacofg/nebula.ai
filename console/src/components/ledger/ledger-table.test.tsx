import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LedgerTable } from "@/components/ledger/ledger-table";
import { renderWithProviders } from "@/test/render";

describe("ledger-table", () => {
  it("renders the usage-ledger columns and selects a row", async () => {
    const user = userEvent.setup();
    const onSelectRow = vi.fn();

    renderWithProviders(
      <LedgerTable
        rows={[
          {
            request_id: "req-001",
            tenant_id: "default",
            requested_model: "openai/gpt-4o-mini",
            final_route_target: "premium",
            final_provider: "openai-compatible",
            fallback_used: false,
            cache_hit: false,
            response_model: "openai/gpt-4o-mini",
            prompt_tokens: 19,
            completion_tokens: 8,
            total_tokens: 27,
            estimated_cost: 0.016,
            latency_ms: 180,
            timestamp: "2026-03-16T22:00:00Z",
            terminal_status: "completed",
            route_reason: "direct_premium_model",
            policy_outcome: "allowed",
          },
        ]}
        selectedRequestId={null}
        onSelectRow={onSelectRow}
        isLoading={false}
      />,
    );

    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Latency")).toBeInTheDocument();
    expect(screen.getByText("Estimated cost")).toBeInTheDocument();

    await user.click(screen.getByText("premium"));
    expect(onSelectRow).toHaveBeenCalledWith("req-001");
  });
});
