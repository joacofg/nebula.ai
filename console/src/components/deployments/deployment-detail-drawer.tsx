"use client";

import { LoaderCircle, PanelRightOpen } from "lucide-react";

import type { DeploymentRecord } from "@/lib/admin-api";
import { RemoteActionCard } from "@/components/deployments/remote-action-card";
import { DeploymentStatusBadge } from "@/components/deployments/deployment-status-badge";
import { FreshnessBadge } from "@/components/deployments/freshness-badge";
import { DependencyHealthPills } from "@/components/deployments/dependency-health-pills";
import { TrustBoundaryCard } from "@/components/hosted/trust-boundary-card";

type DeploymentDetailDrawerProps = {
  deployment: DeploymentRecord;
  isGeneratingToken: boolean;
  onGenerateToken: (deploymentId: string) => void;
  onRequestRevoke: (deploymentId: string) => void;
  onRequestUnlink: (deploymentId: string) => void;
  onClose: () => void;
};

const dateFormatter = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </div>
      <div className="text-sm text-slate-800">{children}</div>
    </div>
  );
}

export function DeploymentDetailDrawer({
  deployment,
  isGeneratingToken,
  onGenerateToken,
  onRequestRevoke,
  onRequestUnlink,
  onClose,
}: DeploymentDetailDrawerProps) {
  const isActive = deployment.enrollment_state === "active";
  const canRelink =
    deployment.enrollment_state === "revoked" || deployment.enrollment_state === "unlinked";

  return (
    <aside className="panel h-full min-h-[32rem] px-5 py-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
            Deployment detail
          </div>
          <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
            {deployment.display_name}
          </h3>
        </div>
        <button type="button" className="secondary-button gap-2 px-3 py-2" onClick={onClose}>
          <PanelRightOpen className="h-4 w-4" />
          Close
        </button>
      </div>

      {/* Freshness section */}
      <div className="mt-6 space-y-2">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Freshness
        </div>
        <FreshnessBadge status={deployment.freshness_status} />
        {deployment.freshness_reason ? (
          <div className="text-sm text-slate-600">{deployment.freshness_reason}</div>
        ) : null}
        {deployment.last_seen_at ? (
          <div className="font-[var(--font-fira-code)] text-xs text-slate-400">
            {dateFormatter.format(new Date(deployment.last_seen_at))}
          </div>
        ) : null}
      </div>

      {/* Identity section */}
      <div className="mt-6 border-t border-border/50 pt-4 space-y-4">
        <Field label="Deployment ID">
          <span className="font-[var(--font-fira-code)] text-xs text-slate-700">
            {deployment.id}
          </span>
        </Field>

        <Field label="Environment">
          <span className="capitalize">{deployment.environment}</span>
        </Field>

        {deployment.nebula_version ? (
          <Field label="Nebula version">
            <span className="font-[var(--font-fira-code)] text-xs">{deployment.nebula_version}</span>
          </Field>
        ) : null}

        {deployment.capability_flags.length > 0 ? (
          <Field label="Capability flags">
            <div className="flex flex-wrap gap-1">
              {deployment.capability_flags.map((flag) => (
                <span
                  key={flag}
                  className="rounded-md bg-slate-100 px-2 py-0.5 font-[var(--font-fira-code)] text-xs text-slate-600"
                >
                  {flag}
                </span>
              ))}
            </div>
          </Field>
        ) : null}

        {/* Enrollment state moved from table to drawer per D-11 */}
        <Field label="Enrollment state">
          <DeploymentStatusBadge state={deployment.enrollment_state} />
        </Field>

        {deployment.enrolled_at ? (
          <Field label="Enrolled at">
            {dateFormatter.format(new Date(deployment.enrolled_at))}
          </Field>
        ) : null}

        <Field label="Created at">
          {dateFormatter.format(new Date(deployment.created_at))}
        </Field>
      </div>

      {/* Dependencies section */}
      <div className="mt-6 border-t border-border/50 pt-4">
        <div className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Dependencies
        </div>
        <DependencyHealthPills summary={deployment.dependency_summary} />
      </div>

      {/* Trust-boundary disclosure card */}
      <div className="mt-6 border-t border-border/50 pt-4">
        <TrustBoundaryCard />
      </div>

      <RemoteActionCard deployment={deployment} />

      {/* Lifecycle actions */}
      <div className="mt-6 border-t border-border/50 pt-4 space-y-2">
        {isActive ? (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="secondary-button"
              onClick={() => onRequestUnlink(deployment.id)}
            >
              Unlink
            </button>
            <button
              type="button"
              className="inline-flex items-center justify-center rounded-xl bg-pink-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-pink-800 focus:outline-none focus:ring-2 focus:ring-pink-400/30"
              onClick={() => onRequestRevoke(deployment.id)}
            >
              Revoke
            </button>
          </div>
        ) : canRelink ? (
          <button
            type="button"
            className="action-button gap-2"
            disabled={isGeneratingToken}
            onClick={() => onGenerateToken(deployment.id)}
          >
            {isGeneratingToken ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
            Generate new token
          </button>
        ) : null}
      </div>
    </aside>
  );
}
