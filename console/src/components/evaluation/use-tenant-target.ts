"use client";

import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getTenantPolicy, listTenants, updateTenantPolicy } from "@/lib/admin-api";
import { queryKeys } from "@/lib/query-keys";
import { snapTarget } from "@/lib/quality-target";
import { useSelectedTenant } from "@/lib/selected-tenant";

/** The thesis headline target: where the slider rests when there is no tenant or its policy failed. */
const FALLBACK_TARGET = 0.95;

type Pick = { tenantId: string | null; value: number };
type Shown = { ready: boolean; target: number };

/**
 * The quality target being explored for the selected tenant, and the way to apply it.
 *
 * The slider opens at the tenant's current `routing_quality_target`. Until the tenant list and the
 * selected tenant's policy have each arrived or failed the hook is not `ready` (the page waits
 * instead of showing a placeholder), and when the operator switches to a tenant whose policy is
 * not cached the target holds its last value rather than passing through 0.95. A pick made on the
 * slider belongs to the tenant it was made for: switching tenant re-opens at that tenant's target.
 * While a save is in flight the target and the tenant are locked, so the confirmation that comes
 * back always describes what is on screen.
 */
export function useTenantTarget(adminKey: string) {
  const queryClient = useQueryClient();
  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey),
    enabled: Boolean(adminKey),
  });
  const { tenantId, setTenantId: select } = useSelectedTenant(tenantsQuery.data);

  // The Política and Playground pages share this query, so a target applied here shows up there.
  const policyEnabled = Boolean(adminKey) && tenantId !== null;
  const policyQuery = useQuery({
    queryKey: queryKeys.tenantPolicy(tenantId ?? "unselected"),
    queryFn: () => getTenantPolicy(adminKey, tenantId ?? ""),
    enabled: policyEnabled,
  });
  const currentTarget = policyQuery.data?.routing_quality_target ?? null;

  const apply = useMutation({
    mutationFn: async ({ id, value }: { id: string; value: number }) => {
      // Read the current policy first: a failed read must not turn into a partial write.
      const policy = await getTenantPolicy(adminKey, id);
      return updateTenantPolicy(adminKey, id, { ...policy, routing_quality_target: value });
    },
    onSuccess: (saved, { id }) => {
      queryClient.setQueryData(queryKeys.tenantPolicy(id), saved);
    },
  });
  const saving = apply.isPending;

  const [pick, setPick] = useState<Pick | null>(null);
  const picked = pick !== null && pick.tenantId === tenantId ? pick.value : null;
  const resolved = picked ?? (currentTarget === null ? FALLBACK_TARGET : snapTarget(currentTarget));

  const settled = !(Boolean(adminKey) && tenantsQuery.isPending) && !(policyEnabled && policyQuery.isPending);
  const [shown, setShown] = useState<Shown>({ ready: false, target: FALLBACK_TARGET });
  if (settled && (!shown.ready || shown.target !== resolved)) {
    setShown({ ready: true, target: resolved });
  }

  return {
    /** The tenant list and the selected tenant's policy have each arrived or failed (once is enough). */
    ready: settled || shown.ready,
    tenants: tenantsQuery.data,
    tenantsError: tenantsQuery.isError ? tenantsQuery.error : null,
    policyError: policyQuery.isError ? policyQuery.error : null,
    tenantId,
    setTenantId: (id: string) => {
      if (saving) {
        return;
      }
      select(id);
      setPick(null);
      apply.reset();
    },
    /** The tenant's own target, as stored; null while unknown. */
    currentTarget,
    /** What the slider shows. */
    target: settled ? resolved : shown.target,
    setTarget: (value: number) => {
      if (saving) {
        return;
      }
      setPick({ tenantId, value });
      apply.reset();
    },
    apply,
    saving,
  };
}

export type TenantTarget = ReturnType<typeof useTenantTarget>;
