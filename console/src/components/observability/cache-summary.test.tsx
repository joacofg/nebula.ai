import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CacheSummary } from "@/components/observability/cache-summary";
import type { CacheControlSummary } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const base: CacheControlSummary = {
  enabled: true,
  similarity_threshold: 0.9,
  max_entry_age_hours: 168,
  runtime_status: "ready",
  runtime_detail: "Qdrant disponible.",
  estimated_hit_rate: 0.38,
  avoided_premium_cost_usd: 0.012345,
  insights: [],
};

describe("CacheSummary", () => {
  it("shows the avoided premium cost with four decimals, as a hit can avoid fractions of a cent", () => {
    renderWithProviders(<CacheSummary cache={base} />);
    expect(screen.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("USD 0.0123");
  });

  it("shows zero avoided cost as USD 0.0000", () => {
    renderWithProviders(<CacheSummary cache={{ ...base, avoided_premium_cost_usd: 0 }} />);
    expect(screen.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("USD 0.0000");
  });
});
