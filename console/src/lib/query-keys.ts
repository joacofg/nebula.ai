import type { UsageLedgerFilters } from "@/lib/admin-api";

export const queryKeys = {
  deployments: ["deployments"] as const,
  deployment: (id: string) => ["deployment", id] as const,
  tenants: ["tenants"] as const,
  apiKeys: (tenantId: string | null = null) => ["api-keys", tenantId ?? "all"] as const,
  tenantPolicy: (tenantId: string) => ["tenant-policy", tenantId] as const,
  policyOptions: ["policy-options"] as const,
  playgroundResponse: (tenantId: string) => ["playground-response", tenantId] as const,
  usageLedger: (filters: UsageLedgerFilters = {}) => ["usage-ledger", filters] as const,
  usageLedgerEntry: (requestId: string) => ["usage-ledger-entry", requestId] as const,
  runtimeHealth: ["runtime-health"] as const,
};
