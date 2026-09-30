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
          <thead className="bg-canvas text-xs font-semibold uppercase tracking-[0.22em] text-ink-4">
            <tr>
              <th className="border-b border-line px-4 py-3">Tenant ID</th>
              <th className="border-b border-line px-4 py-3">Name</th>
              <th className="border-b border-line px-4 py-3">Status</th>
              <th className="border-b border-line px-4 py-3">Updated</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => {
              const selected = tenant.id === selectedTenantId;
              return (
                <tr
                  key={tenant.id}
                  className={[
                    "cursor-pointer transition hover:bg-canvas",
                    selected ? "bg-mark-soft/80" : "",
                  ].join(" ")}
                  onClick={() => onSelectTenant(tenant)}
                >
                  <td className="border-b border-line/70 px-4 py-4 font-(--font-fira-code) text-xs text-ink-2">
                    {tenant.id}
                  </td>
                  <td className="border-b border-line/70 px-4 py-4">
                    <div className="font-semibold text-ink">{tenant.name}</div>
                    <div className="mt-1 text-xs text-ink-4">{tenant.description ?? "No description"}</div>
                  </td>
                  <td className="border-b border-line/70 px-4 py-4">
                    <span
                      className={[
                        "inline-flex rounded-full px-3 py-1 text-xs font-semibold",
                        tenant.active ? "bg-ok-soft text-ok" : "bg-canvas text-ink-3",
                      ].join(" ")}
                    >
                      {tenant.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="border-b border-line/70 px-4 py-4 text-ink-3">
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
