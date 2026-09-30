"use client";

import { useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Plus } from "lucide-react";

import {
  ADMIN_API_KEYS_ENDPOINT,
  createApiKey,
  listApiKeys,
  listTenants,
  revokeApiKey,
  type ApiKeyRecord,
} from "@/lib/admin-api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { CreateApiKeyDialog } from "@/components/api-keys/create-api-key-dialog";
import { ApiKeyTable } from "@/components/api-keys/api-key-table";
import { RevealApiKeyDialog } from "@/components/api-keys/reveal-api-key-dialog";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
import { ErrorAlert } from "@/components/system/state";

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const { adminKey } = useAdminSession();
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [revealedApiKey, setRevealedApiKey] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [pendingRevoke, setPendingRevoke] = useState<ApiKeyRecord | null>(null);

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const apiKeysQuery = useQuery({
    queryKey: queryKeys.apiKeys(selectedTenantId),
    queryFn: () => listApiKeys(adminKey ?? "", selectedTenantId ?? undefined),
    enabled: Boolean(adminKey),
  });

  const createMutation = useMutation({
    mutationFn: async (payload: Parameters<typeof createApiKey>[1]) => {
      if (!adminKey) {
        throw new Error("Operator session missing.");
      }
      return createApiKey(adminKey, payload);
    },
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.apiKeys(selectedTenantId) });
      setCreateOpen(false);
      setRevealedApiKey(response.api_key);
    },
  });

  const revokeMutation = useMutation({
    mutationFn: async (apiKeyId: string) => {
      if (!adminKey) {
        throw new Error("Operator session missing.");
      }
      return revokeApiKey(adminKey, apiKeyId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.apiKeys(selectedTenantId) });
      setRevokingId(null);
    },
    onError: () => {
      setRevokingId(null);
    },
  });

  const tenantOptions = tenantsQuery.data ?? [];
  const apiKeys = useMemo(() => apiKeysQuery.data ?? [], [apiKeysQuery.data]);

  function handleRevoke(apiKey: ApiKeyRecord) {
    setPendingRevoke(apiKey);
  }

  async function confirmRevoke() {
    if (!pendingRevoke) {
      return;
    }
    const apiKey = pendingRevoke;
    setPendingRevoke(null);
    setRevokingId(apiKey.id);
    await revokeMutation.mutateAsync(apiKey.id);
  }

  return (
    <section className="space-y-6">
      <header className="panel flex flex-col gap-4 px-6 py-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">API Keys</div>
          <h2 className="mt-2 font-(--font-fira-code) text-2xl font-semibold text-ink">
            Client credentials and tenant resolution
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-ink-3">
            Operators issue client API keys backed by <span className="font-(--font-fira-code)">{ADMIN_API_KEYS_ENDPOINT}</span>.
            {" "}<span className="font-medium text-ink-2">allowed_tenant_ids</span> defines which tenants a key may use,
            while <span className="font-medium text-ink-2">tenant_id</span> sets the default tenant when public callers omit
            <span className="font-(--font-fira-code)"> X-Nebula-Tenant-ID</span>.
          </p>
          <p className="mt-2 max-w-3xl text-sm text-ink-3">
            If a key authorizes exactly one tenant, Nebula can infer it. If a key intentionally authorizes multiple
            tenants without a default tenant, public callers must send <span className="font-(--font-fira-code)">X-Nebula-Tenant-ID</span>{" "}
            on each request.
          </p>
        </div>

        <button type="button" className="action-button gap-2" onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          Create API key
        </button>
      </header>

      <div className="panel flex flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div className="inline-flex items-center gap-2 text-sm text-ink-2">
          <KeyRound className="h-4 w-4 text-ink-4" />
          Keep revoked records visible so operators can audit historical scope and issuance decisions.
        </div>

        <select
          className="field-input min-w-52"
          value={selectedTenantId ?? ""}
          onChange={(event) => setSelectedTenantId(event.target.value || null)}
        >
          <option value="">All tenants</option>
          {tenantOptions.map((tenant) => (
            <option key={tenant.id} value={tenant.id}>
              {tenant.name}
            </option>
          ))}
        </select>
      </div>

      {apiKeysQuery.isLoading ? (
        <div className="panel px-6 py-8 text-sm text-ink-4">Loading API key inventory...</div>
      ) : apiKeysQuery.isError ? (
        <ErrorAlert error={apiKeysQuery.error} fallback="Unable to load API keys." />
      ) : (
        <ApiKeyTable apiKeys={apiKeys} onRevoke={handleRevoke} revokingId={revokingId} />
      )}

      <CreateApiKeyDialog
        open={createOpen}
        tenants={tenantOptions}
        selectedTenantId={selectedTenantId}
        isSaving={createMutation.isPending}
        onClose={() => setCreateOpen(false)}
        onSubmit={async (payload) => {
          await createMutation.mutateAsync(payload);
        }}
      />

      <AlertDialog open={pendingRevoke !== null} onOpenChange={(open) => (open ? null : setPendingRevoke(null))}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke {pendingRevoke?.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              Callers using this key stop reaching Nebula. The record stays visible for audit.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => void confirmRevoke()}>
              Revoke key
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <RevealApiKeyDialog
        apiKey={revealedApiKey}
        open={revealedApiKey !== null}
        onClose={() => setRevealedApiKey(null)}
      />
    </section>
  );
}
