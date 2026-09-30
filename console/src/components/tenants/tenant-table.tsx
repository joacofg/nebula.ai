import type { TenantRecord } from "@/lib/admin-api";

import { cn } from "cn";

type TenantTableProps = {
  tenants: TenantRecord[];
  selectedTenantId: string | null;
  onSelectTenant: (tenant: TenantRecord) => void;
};

const dateFormatter = new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" });
const HEAD = "px-3 py-2 text-left font-label text-[13px] font-semibold text-ink-2";

export function TenantTable({ tenants, selectedTenantId, onSelectTenant }: TenantTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] table-fixed border-collapse text-sm" aria-label="Tenants">
        <colgroup>
          <col className="w-[34%]" />
          <col className="w-[26%]" />
          <col className="w-[16%]" />
          <col className="w-[24%]" />
        </colgroup>
        <thead>
          <tr className="border-b border-line-strong">
            <th scope="col" className={HEAD}>Nombre</th>
            <th scope="col" className={HEAD}>Id</th>
            <th scope="col" className={HEAD}>Estado</th>
            <th scope="col" className={HEAD}>Actualizado</th>
          </tr>
        </thead>
        <tbody>
          {tenants.map((tenant) => {
            const selected = tenant.id === selectedTenantId;
            return (
              <tr
                key={tenant.id}
                tabIndex={0}
                aria-selected={selected}
                onClick={() => onSelectTenant(tenant)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelectTenant(tenant);
                  }
                }}
                className={cn(
                  "cursor-pointer border-b border-line transition-colors duration-100 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-mark",
                  selected ? "bg-mark-soft/70 shadow-[inset_2px_0_0_var(--color-mark)]" : "hover:bg-canvas",
                )}
              >
                <td className="px-3 py-2.5">
                  <span className="block truncate font-semibold text-ink" title={tenant.name}>
                    {tenant.name}
                  </span>
                  <span className="block truncate text-[13px] text-ink-3" title={tenant.description ?? ""}>
                    {tenant.description || "—"}
                  </span>
                </td>
                <td className="truncate px-3 py-2.5 font-mono text-[12px] text-ink-2" title={tenant.id}>
                  {tenant.id}
                </td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 font-label text-[13px] font-medium text-ink">
                    <span aria-hidden className={cn("size-2 rounded-full", tenant.active ? "bg-ok" : "bg-line-strong/40")} />
                    {tenant.active ? "activo" : "inactivo"}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-ink-3">{dateFormatter.format(new Date(tenant.updated_at))}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
