"use client";

import { useMemo, useState, type ReactNode } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import { cn } from "cn";

import {
  createTenant,
  listTenants,
  updateTenant,
  type TenantInput,
  type TenantRecord,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
import { useSelectedTenant } from "@/lib/selected-tenant";
import { PageHeader } from "@/components/system/page-header";
import { EmptyState, ErrorAlert, LoadingRows } from "@/components/system/state";
import { Button } from "@/components/ui/button";
import { TenantEditorDrawer } from "@/components/tenants/tenant-editor-drawer";
import { TenantTable } from "@/components/tenants/tenant-table";

/** What the drawer holds: a mode and, to edit, the id of the tenant (its record comes from the query). */
type DrawerState = { mode: "create" } | { mode: "edit"; tenantId: string } | { mode: "closed" };

const TENANT_CREATED = "Tenant creado.";

export default function TenantsPage() {
  const queryClient = useQueryClient();
  const { adminKey } = useAdminSession();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  // null until the operator opens or closes the drawer: it then shows the selected tenant.
  const [drawerChoice, setDrawerChoice] = useState<DrawerState | null>(null);
  const [createRequests, setCreateRequests] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const { tenantId: selectedTenantId, setTenantId: setSelectedTenantId } = useSelectedTenant(tenantsQuery.data);
  const drawerState: DrawerState =
    drawerChoice ??
    (selectedTenantId ? { mode: "edit", tenantId: selectedTenantId } : { mode: "create" });
  const editedTenant =
    drawerState.mode === "edit"
      ? (tenantsQuery.data ?? []).find((tenant) => tenant.id === drawerState.tenantId) ?? null
      : null;

  function openCreate() {
    setNotice(null);
    setDrawerChoice({ mode: "create" });
    setCreateRequests((count) => count + 1);
  }

  function openTenant(tenant: TenantRecord) {
    setNotice(null);
    setSelectedTenantId(tenant.id);
    setDrawerChoice({ mode: "edit", tenantId: tenant.id });
  }

  const mutation = useMutation({
    mutationFn: async ({ payload, creating }: { payload: TenantInput; creating: boolean }) => {
      if (!adminKey) {
        throw new Error("Falta la sesión de admin.");
      }
      return creating
        ? createTenant(adminKey, payload)
        : updateTenant(adminKey, payload.id, {
            name: payload.name,
            description: payload.description,
            active: payload.active,
            metadata: payload.metadata,
          });
    },
    onSuccess: async (tenant, { creating }) => {
      // Put the saved record in the list first, so the drawer can read it before the refetch lands.
      queryClient.setQueryData<TenantRecord[]>(queryKeys.tenants, (current = []) =>
        current.some((candidate) => candidate.id === tenant.id)
          ? current.map((candidate) => (candidate.id === tenant.id ? tenant : candidate))
          : [...current, tenant],
      );
      setSelectedTenantId(tenant.id);
      setDrawerChoice({ mode: "edit", tenantId: tenant.id });
      setNotice(creating ? TENANT_CREATED : null);
      await queryClient.invalidateQueries({ queryKey: queryKeys.tenants });
    },
  });

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

  const closeDrawer = () => {
    setNotice(null);
    setDrawerChoice({ mode: "closed" });
  };
  const submitTenant = async (payload: TenantInput, creating: boolean) => {
    await mutation.mutateAsync({ payload, creating });
  };
  // No drawer while the list loads (it would flash a new-tenant form), nor once it was closed.
  let drawer: ReactNode = null;
  if (!tenantsQuery.isLoading && drawerState.mode === "create") {
    drawer = (
      <TenantEditorDrawer
        mode="create"
        tenant={null}
        isSaving={mutation.isPending}
        focusRequest={createRequests}
        onClose={closeDrawer}
        onSubmit={(payload) => submitTenant(payload, true)}
      />
    );
  } else if (!tenantsQuery.isLoading && drawerState.mode === "edit" && editedTenant) {
    drawer = (
      <TenantEditorDrawer
        mode="edit"
        tenant={editedTenant}
        notice={notice}
        isSaving={mutation.isPending}
        onClose={closeDrawer}
        onSubmit={(payload) => submitTenant(payload, false)}
      />
    );
  }

  return (
    <section>
      <PageHeader
        title="Tenants"
        cells={[{ label: "Estado", value: tenantsQuery.data ? `${activeCount} activos` : "—" }]}
        actions={
          <Button type="button" onClick={openCreate}>
            <Plus aria-hidden className="size-4" />
            Crear tenant
          </Button>
        }
      />

      <div className={cn("grid", drawer && "xl:grid-cols-[minmax(0,1fr)_400px]")}>
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
                <Button type="button" variant="outline" onClick={openCreate}>
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
              onSelectTenant={openTenant}
            />
          )}
        </div>

        {drawer ? <div className="border-t border-line xl:border-t-0 xl:border-l">{drawer}</div> : null}
      </div>
    </section>
  );
}
