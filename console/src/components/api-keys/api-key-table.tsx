import type { ApiKeyRecord } from "@/lib/admin-api";

type ApiKeyTableProps = {
  apiKeys: ApiKeyRecord[];
  onRevoke: (apiKey: ApiKeyRecord) => void;
  revokingId: string | null;
};

const dateFormatter = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

function getScopeSummary(apiKey: ApiKeyRecord) {
  const allowedCount = apiKey.allowed_tenant_ids.length;

  if (apiKey.tenant_id) {
    return {
      title: `Auto-resolves ${apiKey.tenant_id}`,
      detail:
        allowedCount > 1
          ? `Authorized for ${allowedCount} tenants total. Public callers can omit X-Nebula-Tenant-ID only when using the default tenant.`
          : "One tenant authorized. Public callers can omit X-Nebula-Tenant-ID.",
    };
  }

  if (allowedCount === 1) {
    return {
      title: `Single allowed tenant: ${apiKey.allowed_tenant_ids[0]}`,
      detail: "Public callers can omit X-Nebula-Tenant-ID because the only authorized tenant is inferred.",
    };
  }

  return {
    title: `${allowedCount} authorized tenants`,
    detail: "Public callers must send X-Nebula-Tenant-ID so Nebula can resolve which authorized tenant to use.",
  };
}

export function ApiKeyTable({ apiKeys, onRevoke, revokingId }: ApiKeyTableProps) {
  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="bg-canvas text-xs font-semibold uppercase tracking-[0.22em] text-ink-4">
            <tr>
              <th className="border-b border-line px-4 py-3">Name</th>
              <th className="border-b border-line px-4 py-3">Key Prefix</th>
              <th className="border-b border-line px-4 py-3">Tenant Scope</th>
              <th className="border-b border-line px-4 py-3">Status</th>
              <th className="border-b border-line px-4 py-3">Created</th>
              <th className="border-b border-line px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {apiKeys.map((apiKey) => {
              const revoked = Boolean(apiKey.revoked_at);
              const scope = getScopeSummary(apiKey);

              return (
                <tr key={apiKey.id} className={revoked ? "bg-canvas/70 text-ink-4" : "hover:bg-canvas"}>
                  <td className="border-b border-line/70 px-4 py-4 font-semibold text-ink">{apiKey.name}</td>
                  <td className="border-b border-line/70 px-4 py-4 font-mono text-xs text-ink-2">
                    {apiKey.key_prefix}
                  </td>
                  <td className="border-b border-line/70 px-4 py-4 text-ink-3">
                    <div className="space-y-1">
                      <div className="font-medium text-ink">{scope.title}</div>
                      <div className="max-w-md text-xs leading-5 text-ink-4">{scope.detail}</div>
                    </div>
                  </td>
                  <td className="border-b border-line/70 px-4 py-4">
                    <span
                      className={[
                        "inline-flex rounded-full px-3 py-1 text-xs font-semibold",
                        revoked ? "bg-canvas text-ink-3" : "bg-ok-soft text-ok",
                      ].join(" ")}
                    >
                      {revoked ? "Revoked" : "Active"}
                    </span>
                  </td>
                  <td className="border-b border-line/70 px-4 py-4 text-ink-3">
                    {dateFormatter.format(new Date(apiKey.created_at))}
                  </td>
                  <td className="border-b border-line/70 px-4 py-4 text-right">
                    <button
                      type="button"
                      className="secondary-button px-3 py-2 text-xs"
                      disabled={revoked || revokingId === apiKey.id}
                      onClick={() => onRevoke(apiKey)}
                    >
                      {revokingId === apiKey.id ? "Revoking..." : "Revoke"}
                    </button>
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
