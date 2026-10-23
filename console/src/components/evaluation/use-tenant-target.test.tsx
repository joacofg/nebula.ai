import type { ReactNode } from "react";

import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useTenantTarget } from "@/components/evaluation/use-tenant-target";
import { AdminApiError, type TenantPolicy, type TenantRecord } from "@/lib/admin-api";
import { SelectedTenantProvider } from "@/lib/selected-tenant";
import { createTestQueryClient } from "@/test/render";

const adminApi = vi.hoisted(() => ({
  listTenants: vi.fn(),
  getTenantPolicy: vi.fn(),
  updateTenantPolicy: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return { ...actual, ...adminApi };
});

function tenant(id: string): TenantRecord {
  return {
    id,
    name: id.toUpperCase(),
    description: null,
    metadata: {},
    active: true,
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  };
}

function policy(target: number): TenantPolicy {
  return {
    routing_mode_default: "auto",
    calibrated_routing_enabled: true,
    allowed_premium_models: [],
    semantic_cache_enabled: true,
    semantic_cache_similarity_threshold: 0.9,
    semantic_cache_max_entry_age_hours: 168,
    fallback_enabled: true,
    max_premium_cost_per_request: null,
    hard_budget_limit_usd: null,
    hard_budget_enforcement: null,
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
    evidence_retention_window: "30d",
    metadata_minimization_level: "standard",
    routing_quality_target: target,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function setup(adminKey = "nebula-admin-key") {
  const queryClient = createTestQueryClient();
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <SelectedTenantProvider>{children}</SelectedTenantProvider>
    </QueryClientProvider>
  );
  return { queryClient, ...renderHook(() => useTenantTarget(adminKey), { wrapper }) };
}

describe("useTenantTarget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    adminApi.listTenants.mockResolvedValue([tenant("a"), tenant("b")]);
    adminApi.getTenantPolicy.mockImplementation(async (_key: string, id: string) => policy(id === "a" ? 0.9 : 0.85));
  });

  it("is not ready until the selected tenant's policy arrives, then reports its target", async () => {
    const pending = deferred<TenantPolicy>();
    adminApi.getTenantPolicy.mockReturnValue(pending.promise);
    const { result } = setup();

    await waitFor(() => expect(adminApi.getTenantPolicy).toHaveBeenCalled());
    expect(result.current.ready).toBe(false);

    await act(async () => pending.resolve(policy(0.9)));
    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.target).toBe(0.9);
    expect(result.current.currentTarget).toBe(0.9);
  });

  it("does not expose mutateAsync, which would skip the settling guard on mutate", async () => {
    const { result } = setup();

    await waitFor(() => expect(result.current.ready).toBe(true));
    expect("mutateAsync" in result.current.apply).toBe(false);
    expect(typeof result.current.apply.mutate).toBe("function");
  });

  it("is ready at 0.95 without a request when there are no tenants", async () => {
    adminApi.listTenants.mockResolvedValue([]);
    const { result } = setup();

    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.target).toBe(0.95);
    expect(adminApi.getTenantPolicy).not.toHaveBeenCalled();
  });

  it("is ready at 0.95 and exposes the error when the tenant list cannot be read", async () => {
    adminApi.listTenants.mockRejectedValue(new AdminApiError(503, "unreachable"));
    const { result } = setup();

    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.target).toBe(0.95);
    expect(result.current.tenantsError).toBeInstanceOf(AdminApiError);
  });

  it("is ready at 0.95 and exposes the error when the policy cannot be read", async () => {
    adminApi.getTenantPolicy.mockRejectedValue(new AdminApiError(503, "unreachable"));
    const { result } = setup();

    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.target).toBe(0.95);
    expect(result.current.currentTarget).toBeNull();
    expect(result.current.policyError).toBeInstanceOf(AdminApiError);
  });

  it("keeps the shown target while the next tenant's policy is pending, instead of falling back to 0.95", async () => {
    const pendingB = deferred<TenantPolicy>();
    adminApi.getTenantPolicy.mockImplementation((_key: string, id: string) =>
      id === "a" ? Promise.resolve(policy(0.9)) : pendingB.promise,
    );
    const { result } = setup();
    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.target).toBe(0.9);

    act(() => result.current.setTenantId("b"));
    expect(result.current.ready).toBe(true);
    expect(result.current.target).toBe(0.9);

    await act(async () => pendingB.resolve(policy(0.85)));
    await waitFor(() => expect(result.current.target).toBe(0.85));
  });

  it("settles while the next tenant's policy is pending, so a held target is not the new tenant's", async () => {
    const pendingB = deferred<TenantPolicy>();
    adminApi.getTenantPolicy.mockImplementation((_key: string, id: string) =>
      id === "a" ? Promise.resolve(policy(0.9)) : pendingB.promise,
    );
    const { result } = setup();
    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.settling).toBe(false);

    act(() => result.current.setTenantId("b"));
    expect(result.current.ready).toBe(true);
    expect(result.current.target).toBe(0.9);
    expect(result.current.settling).toBe(true);

    await act(async () => pendingB.resolve(policy(0.85)));
    await waitFor(() => expect(result.current.settling).toBe(false));
    expect(result.current.target).toBe(0.85);
  });

  it("refuses a new target and an apply while the next tenant's policy is pending, so the held value is never written", async () => {
    const pendingB = deferred<TenantPolicy>();
    adminApi.getTenantPolicy.mockImplementation((_key: string, id: string) =>
      id === "a" ? Promise.resolve(policy(0.9)) : pendingB.promise,
    );
    const { result } = setup();
    await waitFor(() => expect(result.current.target).toBe(0.9));

    act(() => result.current.setTenantId("b"));
    expect(result.current.settling).toBe(true);
    act(() => result.current.setTarget(0.8));
    act(() => result.current.apply.mutate({ id: "b", value: result.current.target }));

    expect(result.current.target).toBe(0.9);
    expect(result.current.saving).toBe(false);
    expect(adminApi.updateTenantPolicy).not.toHaveBeenCalled();

    // Once B's policy is in, the slider opens at B's own target (the refused pick left nothing
    // behind), and both work again.
    await act(async () => pendingB.resolve(policy(0.85)));
    await waitFor(() => expect(result.current.settling).toBe(false));
    expect(result.current.target).toBe(0.85);
    expect(adminApi.updateTenantPolicy).not.toHaveBeenCalled();
    act(() => result.current.setTarget(0.8));
    expect(result.current.target).toBe(0.8);
    adminApi.updateTenantPolicy.mockResolvedValue(policy(0.8));
    act(() => result.current.apply.mutate({ id: "b", value: 0.8 }));
    await waitFor(() => expect(result.current.apply.isSuccess).toBe(true));
    expect(adminApi.updateTenantPolicy).toHaveBeenCalledTimes(1);
  });

  it("does not settle for a tenant whose policy is already cached", async () => {
    const { result } = setup();
    await waitFor(() => expect(result.current.target).toBe(0.9));
    act(() => result.current.setTenantId("b"));
    await waitFor(() => expect(result.current.target).toBe(0.85));

    act(() => result.current.setTenantId("a"));

    expect(result.current.settling).toBe(false);
    expect(result.current.target).toBe(0.9);
  });

  it("is not settling once the policy failed: the target is the 0.95 fallback, not a held value", async () => {
    adminApi.getTenantPolicy.mockRejectedValue(new AdminApiError(503, "unreachable"));
    const { result } = setup();

    await waitFor(() => expect(result.current.policyError).toBeInstanceOf(AdminApiError));
    expect(result.current.settling).toBe(false);
  });

  it("is ready and settled with no admin key, and asks for nothing", async () => {
    const { result } = setup("");

    expect(result.current.ready).toBe(true);
    expect(result.current.settling).toBe(false);
    expect(result.current.target).toBe(0.95);
    expect(adminApi.listTenants).not.toHaveBeenCalled();
    expect(adminApi.getTenantPolicy).not.toHaveBeenCalled();
  });

  it("drops the policy error when the policy later loads", async () => {
    adminApi.getTenantPolicy.mockRejectedValue(new AdminApiError(503, "unreachable"));
    const { result, queryClient } = setup();
    await waitFor(() => expect(result.current.policyError).toBeInstanceOf(AdminApiError));

    adminApi.getTenantPolicy.mockResolvedValue(policy(0.9));
    await act(async () => {
      await queryClient.invalidateQueries();
    });

    await waitFor(() => expect(result.current.policyError).toBeNull());
    expect(result.current.currentTarget).toBe(0.9);
    expect(result.current.target).toBe(0.9);
  });

  it("drops the policy error when the tenant changes", async () => {
    adminApi.getTenantPolicy.mockImplementation(async (_key: string, id: string) => {
      if (id === "a") {
        throw new AdminApiError(503, "unreachable");
      }
      return policy(0.85);
    });
    const { result } = setup();
    await waitFor(() => expect(result.current.policyError).toBeInstanceOf(AdminApiError));

    act(() => result.current.setTenantId("b"));

    expect(result.current.policyError).toBeNull();
    await waitFor(() => expect(result.current.target).toBe(0.85));
    expect(result.current.policyError).toBeNull();
  });

  it("re-opens at a tenant's own target when coming back to it: A, B, A", async () => {
    const { result } = setup();
    await waitFor(() => expect(result.current.target).toBe(0.9));

    act(() => result.current.setTarget(0.8));
    expect(result.current.target).toBe(0.8);

    act(() => result.current.setTenantId("b"));
    await waitFor(() => expect(result.current.target).toBe(0.85));

    act(() => result.current.setTenantId("a"));
    await waitFor(() => expect(result.current.target).toBe(0.9));
  });

  it("does not carry a pick made with no tenant over to the tenants that show up later", async () => {
    adminApi.listTenants.mockResolvedValue([]);
    const { result, queryClient } = setup();
    await waitFor(() => expect(result.current.ready).toBe(true));

    act(() => result.current.setTarget(0.8));
    expect(result.current.target).toBe(0.8);

    adminApi.listTenants.mockResolvedValue([tenant("a")]);
    await act(async () => {
      await queryClient.invalidateQueries();
    });
    await waitFor(() => expect(result.current.tenantId).toBe("a"));
    await waitFor(() => expect(result.current.target).toBe(0.9));
  });

  it("ignores target and tenant changes while a save is in flight", async () => {
    const saving = deferred<TenantPolicy>();
    adminApi.updateTenantPolicy.mockReturnValue(saving.promise);
    const { result } = setup();
    await waitFor(() => expect(result.current.target).toBe(0.9));

    act(() => result.current.setTarget(0.8));
    act(() => result.current.apply.mutate({ id: "a", value: 0.8 }));
    await waitFor(() => expect(result.current.saving).toBe(true));

    act(() => result.current.setTarget(0.7));
    act(() => result.current.setTenantId("b"));
    expect(result.current.target).toBe(0.8);
    expect(result.current.tenantId).toBe("a");
    expect(result.current.saving).toBe(true);

    await act(async () => saving.resolve(policy(0.8)));
    await waitFor(() => expect(result.current.apply.isSuccess).toBe(true));
    expect(result.current.currentTarget).toBe(0.8);
  });
});
