import type { TenantRecord } from "@/lib/admin-api";

type TenantTableProps = {
  tenants: TenantRecord[];
  selectedTenantId: string | null;
  onSelectTenant: (tenant: TenantRecord) => void;
};

const dateFormatter = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function TenantTable({ tenants, selectedTenantId, onSelectTenant }: TenantTableProps) {
  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            <tr>
              <th className="border-b border-border px-4 py-3">Tenant ID</th>
              <th className="border-b border-border px-4 py-3">Name</th>
              <th className="border-b border-border px-4 py-3">Status</th>
              <th className="border-b border-border px-4 py-3">Updated</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => {
              const selected = tenant.id === selectedTenantId;
              return (
                <tr
                  key={tenant.id}
                  className={[
                    "cursor-pointer transition hover:bg-slate-50",
                    selected ? "bg-sky-50/80" : "",
                  ].join(" ")}
                  onClick={() => onSelectTenant(tenant)}
                >
                  <td className="border-b border-border/70 px-4 py-4 font-[var(--font-fira-code)] text-xs text-slate-700">
                    {tenant.id}
                  </td>
                  <td className="border-b border-border/70 px-4 py-4">
                    <div className="font-semibold text-slate-950">{tenant.name}</div>
                    <div className="mt-1 text-xs text-slate-500">{tenant.description ?? "No description"}</div>
                  </td>
                  <td className="border-b border-border/70 px-4 py-4">
                    <span
                      className={[
                        "inline-flex rounded-full px-3 py-1 text-xs font-semibold",
                        tenant.active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600",
                      ].join(" ")}
                    >
                      {tenant.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="border-b border-border/70 px-4 py-4 text-slate-600">
                    {dateFormatter.format(new Date(tenant.updated_at))}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
