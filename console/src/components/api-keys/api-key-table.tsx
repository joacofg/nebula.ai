import type { ApiKeyRecord } from "@/lib/admin-api";

import { Button } from "@/components/ui/button";

type ApiKeyTableProps = {
  apiKeys: ApiKeyRecord[];
  onRevoke: (apiKey: ApiKeyRecord) => void;
  revokingId: string | null;
};

const dateFormatter = new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short", hourCycle: "h23" });
const HEAD = "px-3 py-2 text-left font-label text-[13px] font-semibold text-ink-2";

function getScopeSummary(apiKey: ApiKeyRecord) {
  const allowedCount = apiKey.allowed_tenant_ids.length;
  if (apiKey.tenant_id) {
    return {
      title: `Por defecto: ${apiKey.tenant_id}`,
      detail: allowedCount > 1 ? `${allowedCount} tenants permitidos; sin header va al de defecto.` : "Un tenant; el header es opcional.",
    };
  }
  if (allowedCount === 1) {
    return { title: `Único tenant: ${apiKey.allowed_tenant_ids[0]}`, detail: "El header X-Nebula-Tenant-ID es opcional." };
  }
  return { title: `${allowedCount} tenants permitidos`, detail: "Los pedidos tienen que enviar X-Nebula-Tenant-ID." };
}

export function ApiKeyTable({ apiKeys, onRevoke, revokingId }: ApiKeyTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[680px] table-fixed border-collapse text-sm" aria-label="Claves de API">
        <colgroup>
          <col className="w-[26%]" />
          <col />
          <col className="w-[11%]" />
          <col className="w-[14%]" />
          <col className="w-[110px]" />
        </colgroup>
        <thead>
          <tr className="border-b border-line-strong">
            <th scope="col" className={HEAD}>Nombre</th>
            <th scope="col" className={HEAD}>Alcance</th>
            <th scope="col" className={HEAD}>Estado</th>
            <th scope="col" className={HEAD}>Creada</th>
            <th scope="col" className={HEAD}>
              <span className="sr-only">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {apiKeys.map((apiKey) => {
            const revoked = Boolean(apiKey.revoked_at);
            const scope = getScopeSummary(apiKey);
            return (
              <tr key={apiKey.id} className={revoked ? "border-b border-line text-ink-3" : "border-b border-line hover:bg-canvas"}>
                <td className="px-3 py-2.5">
                  <span className={`block truncate font-semibold ${revoked ? "text-ink-3" : "text-ink"}`} title={apiKey.name}>
                    {apiKey.name}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <div className="truncate font-medium text-ink" title={`${scope.title}. ${scope.detail}`}>
                    {scope.title}
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 font-label text-[13px] font-medium text-ink">
                    <span aria-hidden className={`size-2 rounded-full ${revoked ? "bg-line-strong/40" : "bg-ok"}`} />
                    {revoked ? "revocada" : "activa"}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-ink-3">{dateFormatter.format(new Date(apiKey.created_at))}</td>
                <td className="px-3 py-2.5 text-right">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={revoked || revokingId === apiKey.id}
                    onClick={() => onRevoke(apiKey)}
                  >
                    {revokingId === apiKey.id ? "Revocando…" : "Revocar"}
                  </Button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
