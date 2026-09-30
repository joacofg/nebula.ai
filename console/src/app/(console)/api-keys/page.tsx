"use client";

import { useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import {
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
import { PageHeader } from "@/components/system/page-header";
import { EmptyState, ErrorAlert, LoadingRows } from "@/components/system/state";
import { Button } from "@/components/ui/button";

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
        throw new Error("Falta la sesión de admin.");
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
        throw new Error("Falta la sesión de admin.");
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

  const tenantFilter = (
    <select
      aria-label="Tenant"
      className="h-9 min-w-52 rounded-[2px] border border-line bg-surface px-2 text-[15px] font-semibold text-ink"
      value={selectedTenantId ?? ""}
      onChange={(event) => setSelectedTenantId(event.target.value || null)}
    >
      <option value="">Todos los tenants</option>
      {tenantOptions.map((tenant) => (
        <option key={tenant.id} value={tenant.id}>
          {tenant.name}
        </option>
      ))}
    </select>
  );

  return (
    <section>
      <PageHeader
        title="Claves de API"
        cells={[
          { label: "Tenant", value: tenantFilter },
          { label: "Activas", value: apiKeysQuery.data ? String(apiKeys.filter((k) => !k.revoked_at).length) : "—" },
        ]}
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus aria-hidden className="size-4" />
            Crear clave
          </Button>
        }
      />

      <div className="px-6 py-5">
        {apiKeysQuery.isLoading ? (
          <LoadingRows rows={6} label="Cargando claves" />
        ) : apiKeysQuery.isError ? (
          <ErrorAlert error={apiKeysQuery.error} fallback="No se pudieron cargar las claves." />
        ) : apiKeys.length === 0 ? (
          <EmptyState
            title="Todavía no hay claves."
            action={
              <Button type="button" variant="outline" onClick={() => setCreateOpen(true)}>
                Crear clave
              </Button>
            }
          />
        ) : (
          <ApiKeyTable apiKeys={apiKeys} onRevoke={handleRevoke} revokingId={revokingId} />
        )}
      </div>

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
            <AlertDialogTitle>¿Revocar {pendingRevoke?.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              Los clientes que la usan dejan de llegar a Nebula. El registro queda visible.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => void confirmRevoke()}>
              Revocar clave
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
