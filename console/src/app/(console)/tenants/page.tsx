"use client";

import { useEffect, useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, SlidersHorizontal } from "lucide-react";

import {
  ADMIN_TENANTS_ENDPOINT,
  createTenant,
  listTenants,
  updateTenant,
  type TenantInput,
  type TenantRecord,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
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
        throw new Error("Operator session missing.");
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

  return (
    <section className="space-y-6">
      <header className="panel flex flex-col gap-4 px-6 py-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Tenants</div>
          <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
            Tenant operations
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Tenants are Nebula&apos;s enforced runtime boundary for policy, request attribution, and usage.
            Use API keys to segment which callers can reach each tenant, and treat app or workload names as
            team conventions you capture in tenant names, key names, or notes rather than as product objects.
          </p>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            This console surface stays grounded in <span className="font-[var(--font-fira-code)]">{ADMIN_TENANTS_ENDPOINT}</span>: create real tenant records here, then issue tenant-scoped API keys separately when you need caller-specific access.
          </p>
        </div>
        <button
          type="button"
          className="action-button gap-2"
          onClick={() => setDrawerState({ mode: "create", tenant: null })}
        >
          <Plus className="h-4 w-4" />
          Create tenant
        </button>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.95fr)]">
        <div className="space-y-4">
          <div className="panel flex flex-col gap-4 px-5 py-4 md:flex-row md:items-center">
            <label className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                className="field-input pl-9"
                placeholder="Search tenant id or name"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>

            <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <SlidersHorizontal className="h-4 w-4 text-slate-400" />
              <select
                className="field-input min-w-36"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}
              >
                <option value="all">All statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </label>
          </div>

          {tenantsQuery.isLoading ? (
            <div className="panel px-6 py-8 text-sm text-slate-500">Loading tenant inventory...</div>
          ) : tenantsQuery.isError ? (
            <div className="panel border-rose-200 bg-rose-50 px-6 py-8 text-sm text-rose-900">
              {tenantsQuery.error instanceof Error ? tenantsQuery.error.message : "Unable to load tenants."}
            </div>
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
    </section>
  );
}
