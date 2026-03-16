export const queryKeys = {
  tenants: ["tenants"] as const,
  apiKeys: (tenantId: string | null = null) => ["api-keys", tenantId ?? "all"] as const,
  tenantPolicy: (tenantId: string) => ["tenant-policy", tenantId] as const,
  policyOptions: ["policy-options"] as const,
};
