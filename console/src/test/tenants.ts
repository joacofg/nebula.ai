import type { TenantRecord } from "@/lib/admin-api";

/** The tenant most console tests need; spread over it for the fields a test cares about. */
export const TENANT_A: TenantRecord = {
  id: "tenant-a",
  name: "Tenant A",
  description: "Primary",
  metadata: {},
  active: true,
  created_at: "2026-03-16T12:00:00Z",
  updated_at: "2026-03-16T12:00:00Z",
};
