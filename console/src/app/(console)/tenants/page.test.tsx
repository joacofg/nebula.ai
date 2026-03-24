import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/admin-session-provider", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/admin-session-provider")>();
  return {
    ...actual,
    useAdminSession: vi.fn(),
  };
});

vi.mock("@/lib/admin-api", () => ({
  ADMIN_TENANTS_ENDPOINT: "/v1/admin/tenants",
  createTenant: vi.fn(),
  listTenants: vi.fn(),
  updateTenant: vi.fn(),
}));

import TenantsPage from "@/app/(console)/tenants/page";
import { useAdminSession } from "@/lib/admin-session-provider";
import { listTenants } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const mockedUseAdminSession = vi.mocked(useAdminSession);
const mockedListTenants = vi.mocked(listTenants);

beforeEach(() => {
  mockedUseAdminSession.mockReturnValue({
    adminKey: "admin-key",
    setAdminKey: vi.fn(),
    clearAdminKey: vi.fn(),
    status: "authenticated",
  });

  mockedListTenants.mockResolvedValue([
    {
      id: "tenant-a",
      name: "Tenant A",
      description: "Primary tenant",
      metadata: {},
      active: true,
      created_at: "2026-03-16T12:00:00Z",
      updated_at: "2026-03-16T12:00:00Z",
    },
  ]);
});

describe("tenants page", () => {
  it("explains tenant and API-key runtime truth without inventing app objects", async () => {
    renderWithProviders(<TenantsPage />);

    expect(await screen.findByRole("heading", { name: "Tenant operations" })).toBeInTheDocument();
    expect(
      screen.getByText(/Tenants are Nebula's enforced runtime boundary for policy, request attribution, and usage/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Use API keys to segment which callers can reach each tenant/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/treat app or workload names as team conventions/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/create real tenant records here, then issue tenant-scoped API keys separately/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/workspace/i)).not.toBeInTheDocument();
  });
});
