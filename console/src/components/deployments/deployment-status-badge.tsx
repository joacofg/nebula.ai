import type { EnrollmentState } from "@/lib/admin-api";

type DeploymentStatusBadgeProps = {
  state: EnrollmentState;
};

const STATE_STYLES: Record<EnrollmentState, { className: string; label: string }> = {
  pending: {
    className: "bg-amber-50 text-amber-700 border-amber-200",
    label: "Pending enrollment",
  },
  active: {
    className: "bg-sky-50 text-sky-700 border-sky-200",
    label: "Active",
  },
  revoked: {
    className: "bg-rose-50 text-rose-700 border-rose-200",
    label: "Revoked",
  },
  unlinked: {
    className: "bg-slate-100 text-slate-600 border-slate-200",
    label: "Unlinked",
  },
};

export function DeploymentStatusBadge({ state }: DeploymentStatusBadgeProps) {
  const { className, label } = STATE_STYLES[state] ?? STATE_STYLES.pending;
  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2 py-1 text-xs font-semibold",
        className,
      ].join(" ")}
    >
      {label}
    </span>
  );
}
