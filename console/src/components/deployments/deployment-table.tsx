import type { DeploymentRecord } from "@/lib/admin-api";
import { DeploymentStatusBadge } from "@/components/deployments/deployment-status-badge";

type DeploymentTableProps = {
  deployments: DeploymentRecord[];
  selectedDeploymentId: string | null;
  onSelectDeployment: (deployment: DeploymentRecord) => void;
};

const dateFormatter = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const ENV_LABELS: Record<string, string> = {
  production: "Production",
  staging: "Staging",
  development: "Development",
};

export function DeploymentTable({
  deployments,
  selectedDeploymentId,
  onSelectDeployment,
}: DeploymentTableProps) {
  if (deployments.length === 0) {
    return (
      <div className="panel px-6 py-12 text-center">
        <p className="font-[var(--font-fira-code)] text-base font-semibold text-slate-950">
          No deployments linked
        </p>
        <p className="mt-2 text-sm text-slate-500">
          Create a deployment slot to start the enrollment flow and link a self-hosted gateway.
        </p>
      </div>
    );
  }

  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            <tr>
              <th className="border-b border-border px-4 py-3">Name</th>
              <th className="border-b border-border px-4 py-3">Environment</th>
              <th className="border-b border-border px-4 py-3">Status</th>
              <th className="border-b border-border px-4 py-3">Enrolled</th>
            </tr>
          </thead>
          <tbody>
            {deployments.map((deployment) => {
              const selected = deployment.id === selectedDeploymentId;
              return (
                <tr
                  key={deployment.id}
                  className={[
                    "cursor-pointer transition hover:bg-slate-50",
                    selected ? "bg-sky-50" : "",
                  ].join(" ")}
                  onClick={() => onSelectDeployment(deployment)}
                >
                  <td className="border-b border-border/70 px-4 py-4">
                    <div className="font-semibold text-slate-950">{deployment.display_name}</div>
                    <div className="mt-0.5 font-[var(--font-fira-code)] text-xs text-slate-400">
                      {deployment.id}
                    </div>
                  </td>
                  <td className="border-b border-border/70 px-4 py-4 text-slate-600">
                    {ENV_LABELS[deployment.environment] ?? deployment.environment}
                  </td>
                  <td className="border-b border-border/70 px-4 py-4">
                    <DeploymentStatusBadge state={deployment.enrollment_state} />
                  </td>
                  <td className="border-b border-border/70 px-4 py-4 text-slate-500">
                    {deployment.enrolled_at
                      ? dateFormatter.format(new Date(deployment.enrolled_at))
                      : "—"}
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
