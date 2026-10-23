"use client";

import { useState } from "react";

import { useQuery } from "@tanstack/react-query";

import { getTenantPolicy, listTenants } from "@/lib/admin-api";
import { queryKeys } from "@/lib/query-keys";
import { snapTarget } from "@/lib/quality-target";
import { useSelectedTenant } from "@/lib/selected-tenant";

/** The thesis headline target: where the slider rests until the tenant's own target is known. */
const FALLBACK_TARGET = 0.95;

type Pick = { tenantId: string | null; value: number };

/**
 * The quality target being explored for the selected tenant. The slider opens at the tenant's
 * current `routing_quality_target`; once the operator moves it, their pick wins until they switch
 * tenant, which re-opens it at that tenant's target.
 */
export function useTenantTarget(adminKey: string) {
  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey),
    enabled: Boolean(adminKey),
  });
  const { tenantId, setTenantId } = useSelectedTenant(tenantsQuery.data);

  // The Política and Playground pages share this query, so a target applied here shows up there.
  const policyQuery = useQuery({
    queryKey: queryKeys.tenantPolicy(tenantId ?? "unselected"),
    queryFn: () => getTenantPolicy(adminKey, tenantId ?? ""),
    enabled: Boolean(adminKey) && tenantId !== null,
  });
  const currentTarget = policyQuery.data?.routing_quality_target ?? null;

  const [pick, setPick] = useState<Pick | null>(null);
  // A pick made before the tenant list arrived belongs to whichever tenant resolves first.
  const picked = pick !== null && (pick.tenantId === null || pick.tenantId === tenantId) ? pick.value : null;
  const target = picked ?? (currentTarget === null ? FALLBACK_TARGET : snapTarget(currentTarget));

  return {
    tenants: tenantsQuery.data,
    tenantsError: tenantsQuery.isError ? tenantsQuery.error : null,
    tenantId,
    setTenantId,
    currentTarget,
    target,
    setTarget: (value: number) => setPick({ tenantId, value }),
  };
}

export type TenantTarget = ReturnType<typeof useTenantTarget>;
