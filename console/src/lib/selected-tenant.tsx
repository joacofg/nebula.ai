"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { TenantRecord } from "@/lib/admin-api";

type SelectedTenantContextValue = {
  selectedId: string | null;
  select: (id: string) => void;
};

const SelectedTenantContext = createContext<SelectedTenantContextValue | null>(null);

/**
 * Holds the tenant the operator is working with, in memory only like the admin session, so that
 * moving between pages keeps it. It lives in the console layout: signing out drops it.
 */
export function SelectedTenantProvider({ children }: { children: ReactNode }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const value = useMemo(() => ({ selectedId, select: setSelectedId }), [selectedId]);
  return <SelectedTenantContext.Provider value={value}>{children}</SelectedTenantContext.Provider>;
}

/**
 * The shared tenant, resolved against the page's tenant list. With no valid selection (none yet,
 * or an id the list no longer has) it is the first tenant, which is stored. While the list is
 * loading or empty everything is null and the stored choice is left alone.
 */
export function useSelectedTenant(tenants: TenantRecord[] | undefined): {
  tenantId: string | null;
  tenant: TenantRecord | null;
  setTenantId: (id: string) => void;
} {
  const context = useContext(SelectedTenantContext);
  if (!context) {
    throw new Error("useSelectedTenant must be used inside SelectedTenantProvider.");
  }
  const { selectedId, select } = context;

  const tenant = tenants?.find((candidate) => candidate.id === selectedId) ?? tenants?.[0] ?? null;
  const tenantId = tenant?.id ?? null;

  useEffect(() => {
    if (tenantId && tenantId !== selectedId) {
      select(tenantId);
    }
  }, [tenantId, selectedId, select]);

  return { tenantId, tenant, setTenantId: select };
}
