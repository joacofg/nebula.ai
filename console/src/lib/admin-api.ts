"use client";

export type RoutingMode = "auto" | "local_only" | "premium_only";

export type TenantPolicy = {
  routing_mode_default: RoutingMode;
  allowed_premium_models: string[];
  semantic_cache_enabled: boolean;
  fallback_enabled: boolean;
  max_premium_cost_per_request: number | null;
  soft_budget_usd: number | null;
  prompt_capture_enabled: boolean;
  response_capture_enabled: boolean;
};

export type TenantRecord = {
  id: string;
  name: string;
  description: string | null;
  metadata: Record<string, unknown>;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type TenantInput = {
  id: string;
  name: string;
  description: string;
  metadata: Record<string, unknown>;
  active: boolean;
};

export type ApiKeyRecord = {
  id: string;
  name: string;
  key_prefix: string;
  tenant_id: string | null;
  allowed_tenant_ids: string[];
  revoked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiKeyCreateInput = {
  name: string;
  tenant_id: string | null;
  allowed_tenant_ids: string[];
};

export type ApiKeyCreateResponse = {
  api_key: string;
  record: ApiKeyRecord;
};

export type PolicyOptionsResponse = {
  routing_modes: RoutingMode[];
  known_premium_models: string[];
  default_premium_model: string;
};

type RequestOptions = {
  adminKey: string;
  method?: "GET" | "POST" | "PATCH" | "PUT";
  body?: unknown;
};

async function adminRequest<T>(path: string, options: RequestOptions): Promise<T> {
  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Nebula-Admin-Key": options.adminKey,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    cache: "no-store",
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? "Nebula admin request failed.");
  }

  return (await response.json()) as T;
}

export const ADMIN_TENANTS_ENDPOINT = "/api/admin/tenants";
export const ADMIN_API_KEYS_ENDPOINT = "/api/admin/api-keys";

export function listTenants(adminKey: string) {
  return adminRequest<TenantRecord[]>(ADMIN_TENANTS_ENDPOINT, { adminKey });
}

export function createTenant(adminKey: string, payload: TenantInput) {
  return adminRequest<TenantRecord>(ADMIN_TENANTS_ENDPOINT, {
    adminKey,
    method: "POST",
    body: payload,
  });
}

export function updateTenant(adminKey: string, tenantId: string, payload: Omit<TenantInput, "id">) {
  return adminRequest<TenantRecord>(`${ADMIN_TENANTS_ENDPOINT}/${tenantId}`, {
    adminKey,
    method: "PATCH",
    body: payload,
  });
}

export function listApiKeys(adminKey: string, tenantId?: string) {
  const query = tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : "";
  return adminRequest<ApiKeyRecord[]>(`${ADMIN_API_KEYS_ENDPOINT}${query}`, { adminKey });
}

export function createApiKey(adminKey: string, payload: ApiKeyCreateInput) {
  return adminRequest<ApiKeyCreateResponse>(ADMIN_API_KEYS_ENDPOINT, {
    adminKey,
    method: "POST",
    body: payload,
  });
}

export function revokeApiKey(adminKey: string, apiKeyId: string) {
  return adminRequest<ApiKeyRecord>(`${ADMIN_API_KEYS_ENDPOINT}/${apiKeyId}/revoke`, {
    adminKey,
    method: "POST",
  });
}

export function getTenantPolicy(adminKey: string, tenantId: string) {
  return adminRequest<TenantPolicy>(`${ADMIN_TENANTS_ENDPOINT}/${tenantId}/policy`, { adminKey });
}

export function updateTenantPolicy(adminKey: string, tenantId: string, payload: TenantPolicy) {
  return adminRequest<TenantPolicy>(`${ADMIN_TENANTS_ENDPOINT}/${tenantId}/policy`, {
    adminKey,
    method: "PUT",
    body: payload,
  });
}

export function getPolicyOptions(adminKey: string) {
  return adminRequest<PolicyOptionsResponse>("/api/admin/policy/options", { adminKey });
}
