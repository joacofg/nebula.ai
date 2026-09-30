"use client";

import { useEffect, useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";

import {
  createTenant,
  listTenants,
  updateTenant,
  type TenantInput,
  type TenantRecord,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
import { PageHeader } from "@/components/system/page-header";
import { EmptyState, ErrorAlert, LoadingRows } from "@/components/system/state";
import { Button } from "@/components/ui/button";
import { TenantEditorDrawer } from "@/components/tenants/tenant-editor-drawer";
import { TenantTable } from "@/components/tenants/tenant-table";

type DrawerState =
  | { mode: "create"; tenant: null }
  | { mode: "edit"; tenant: TenantRecord | null };

export default function TenantsPage() {
  const queryClient = useQueryClient();
  const { adminKey } = useAdminSession();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [drawerState, setDrawerState] = useState<DrawerState>({ mode: "create", tenant: null });

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const mutation = useMutation({
    mutationFn: async (payload: TenantInput) => {
      if (!adminKey) {
        throw new Error("Falta la sesión de admin.");
      }
      return drawerState.mode === "create"
        ? createTenant(adminKey, payload)
        : updateTenant(adminKey, payload.id, {
            name: payload.name,
            description: payload.description,
            active: payload.active,
            metadata: payload.metadata,
          });
    },
    onSuccess: async (tenant) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.tenants });
      setSelectedTenantId(tenant.id);
      setDrawerState({ mode: "edit", tenant });
    },
  });

  useEffect(() => {
    if (!tenantsQuery.data?.length) {
      return;
    }
    if (!selectedTenantId) {
      const firstTenant = tenantsQuery.data[0];
      setSelectedTenantId(firstTenant.id);
      setDrawerState({ mode: "edit", tenant: firstTenant });
      return;
    }
    const nextTenant = tenantsQuery.data.find((tenant) => tenant.id === selectedTenantId);
    if (nextTenant) {
      setDrawerState({ mode: "edit", tenant: nextTenant });
    }
  }, [selectedTenantId, tenantsQuery.data]);

  const filteredTenants = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    return (tenantsQuery.data ?? []).filter((tenant) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        tenant.id.toLowerCase().includes(normalizedSearch) ||
        tenant.name.toLowerCase().includes(normalizedSearch);
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && tenant.active) ||
        (statusFilter === "inactive" && !tenant.active);
      return matchesSearch && matchesStatus;
    });
  }, [searchTerm, statusFilter, tenantsQuery.data]);

  const activeCount = (tenantsQuery.data ?? []).filter((tenant) => tenant.active).length;

  return (
    <section>
      <PageHeader
        title="Tenants"
        cells={[{ label: "Estado", value: tenantsQuery.data ? `${activeCount} activos` : "—" }]}
        actions={
          <Button type="button" onClick={() => setDrawerState({ mode: "create", tenant: null })}>
            <Plus aria-hidden className="size-4" />
            Crear tenant
          </Button>
        }
      />

      <div className="grid xl:grid-cols-[minmax(0,1fr)_400px]">
        <div className="flex min-w-0 flex-col gap-4 px-6 py-5">
          <div className="flex flex-wrap items-center gap-3">
            <label className="relative min-w-64 flex-1">
              <span className="sr-only">Buscar</span>
              <Search aria-hidden className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-3" />
              <input
                className="field-input pl-9"
                placeholder="Buscar por id o nombre"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>
            <label className="flex items-center gap-2">
              <span className="font-label text-[13px] font-medium text-ink-3">Estado</span>
              <select
                className="field-input min-w-36"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}
              >
                <option value="all">Todos</option>
                <option value="active">Activos</option>
                <option value="inactive">Inactivos</option>
              </select>
            </label>
          </div>

          {tenantsQuery.isLoading ? (
            <LoadingRows rows={6} label="Cargando tenants" />
          ) : tenantsQuery.isError ? (
            <ErrorAlert error={tenantsQuery.error} fallback="No se pudieron cargar los tenants." />
          ) : (tenantsQuery.data ?? []).length === 0 ? (
            <EmptyState
              title="Todavía no hay tenants."
              action={
                <Button type="button" variant="outline" onClick={() => setDrawerState({ mode: "create", tenant: null })}>
                  Crear tenant
                </Button>
              }
            />
          ) : filteredTenants.length === 0 ? (
            <EmptyState title="Sin resultados." />
          ) : (
            <TenantTable
              tenants={filteredTenants}
              selectedTenantId={selectedTenantId}
              onSelectTenant={(tenant) => {
                setSelectedTenantId(tenant.id);
                setDrawerState({ mode: "edit", tenant });
              }}
            />
          )}
        </div>

        <div className="border-t border-line xl:border-t-0 xl:border-l">
          <TenantEditorDrawer
            mode={drawerState.mode}
            tenant={drawerState.tenant}
            isSaving={mutation.isPending}
            onClose={() => setDrawerState({ mode: "edit", tenant: drawerState.tenant })}
            onSubmit={async (payload) => {
              await mutation.mutateAsync(payload);
            }}
          />
        </div>
      </div>
    </section>
  );
}
