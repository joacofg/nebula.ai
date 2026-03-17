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
  runtime_enforced_fields: string[];
  soft_signal_fields: string[];
  advisory_fields: string[];
};

export type PlaygroundInput = {
  tenantId: string;
  model: string;
  prompt: string;
};

export type PlaygroundUsage = {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
};

export type PlaygroundResponse = {
  id: string;
  object: "chat.completion";
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: "assistant";
      content: string;
    };
    finish_reason: "stop" | "length" | "content_filter" | "tool_calls";
  }>;
  usage: PlaygroundUsage;
  system_fingerprint: string | null;
  request_id?: string | null;
};

export type PlaygroundCompletionResult = {
  body: PlaygroundResponse | null;
  errorDetail: string | null;
  status: number;
  requestId: string;
  tenantId: string;
  routeTarget: string;
  routeReason: string;
  provider: string;
  cacheHit: boolean;
  fallbackUsed: boolean;
  policyMode: string;
  policyOutcome: string;
};

export type UsageLedgerRecord = {
  request_id: string;
  tenant_id: string;
  requested_model: string;
  final_route_target: string;
  final_provider: string | null;
  fallback_used: boolean;
  cache_hit: boolean;
  response_model: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number | null;
  latency_ms: number | null;
  timestamp: string;
  terminal_status: string;
  route_reason: string | null;
  policy_outcome: string | null;
};

export type UsageLedgerFilters = {
  tenantId?: string;
  routeTarget?: string;
  terminalStatus?: string;
  fromTimestamp?: string;
  toTimestamp?: string;
  requestId?: string;
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
export const ADMIN_USAGE_LEDGER_ENDPOINT = "/api/admin/usage/ledger";

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

export async function createPlaygroundCompletion(
  adminKey: string,
  payload: PlaygroundInput,
): Promise<PlaygroundCompletionResult> {
  const response = await fetch("/api/playground/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Nebula-Admin-Key": adminKey,
    },
    body: JSON.stringify({
      tenant_id: payload.tenantId,
      model: payload.model,
      messages: [{ role: "user", content: payload.prompt }],
      stream: false,
    }),
    cache: "no-store",
  });

  const responseBody = (await response.json().catch(() => ({}))) as PlaygroundResponse & {
    detail?: string;
  };
  const isSuccess = response.ok;
  return {
    body: isSuccess ? responseBody : null,
    errorDetail: isSuccess ? null : responseBody.detail ?? "Nebula playground request failed.",
    status: response.status,
    requestId: response.headers.get("X-Request-ID") ?? responseBody.request_id ?? "",
    tenantId: response.headers.get("X-Nebula-Tenant-ID") ?? payload.tenantId,
    routeTarget: response.headers.get("X-Nebula-Route-Target") ?? "",
    routeReason: response.headers.get("X-Nebula-Route-Reason") ?? "",
    provider: response.headers.get("X-Nebula-Provider") ?? "",
    cacheHit: response.headers.get("X-Nebula-Cache-Hit") === "true",
    fallbackUsed: response.headers.get("X-Nebula-Fallback-Used") === "true",
    policyMode: response.headers.get("X-Nebula-Policy-Mode") ?? "",
    policyOutcome: response.headers.get("X-Nebula-Policy-Outcome") ?? "",
  };
}

function buildUsageLedgerQuery(filters: UsageLedgerFilters) {
  const searchParams = new URLSearchParams();
  if (filters.tenantId) {
    searchParams.set("tenant_id", filters.tenantId);
  }
  if (filters.routeTarget) {
    searchParams.set("route_target", filters.routeTarget);
  }
  if (filters.terminalStatus) {
    searchParams.set("terminal_status", filters.terminalStatus);
  }
  if (filters.fromTimestamp) {
    searchParams.set("from_timestamp", filters.fromTimestamp);
  }
  if (filters.toTimestamp) {
    searchParams.set("to_timestamp", filters.toTimestamp);
  }
  if (filters.requestId) {
    searchParams.set("request_id", filters.requestId);
  }
  const query = searchParams.toString();
  return query.length > 0 ? `?${query}` : "";
}

export function listUsageLedger(adminKey: string, filters: UsageLedgerFilters = {}) {
  return adminRequest<UsageLedgerRecord[]>(
    `${ADMIN_USAGE_LEDGER_ENDPOINT}${buildUsageLedgerQuery(filters)}`,
    { adminKey },
  );
}

export async function getUsageLedgerEntry(adminKey: string, requestId: string) {
  const entries = await listUsageLedger(adminKey, { requestId });
  return entries[0] ?? null;
}
