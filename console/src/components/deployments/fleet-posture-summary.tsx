import type { DeploymentRecord } from "@/lib/admin-api";
import { summarizeFleetPosture } from "@/components/deployments/fleet-posture";
import { getHostedContractContent } from "@/lib/hosted-contract";

type FleetPostureSummaryProps = {
  deployments: DeploymentRecord[];
};

type SummaryCard = {
  title: string;
  count: number;
  detail: string;
  accentClassName: string;
};

function formatDeploymentCount(count: number) {
  return `${count} deployment${count === 1 ? "" : "s"}`;
}

export function FleetPostureSummary({ deployments }: FleetPostureSummaryProps) {
  const summary = summarizeFleetPosture(deployments);
  const { reinforcement } = getHostedContractContent();

  const cards: SummaryCard[] = [
    {
      title: "Linked and current",
      count: summary.counts.linked,
      detail:
        summary.counts.linked > 0
          ? "Linked deployments with current metadata visibility for hosted fleet posture."
          : "No deployments currently report linked, current metadata visibility.",
      accentClassName: "border-emerald-200 bg-emerald-50/80 text-emerald-950",
    },
    {
      title: "Pending enrollment",
      count: summary.counts.pendingEnrollment,
      detail:
        summary.counts.pendingEnrollment > 0
          ? "Enrollment is still pending, so hosted visibility remains descriptive and incomplete."
          : "No deployments are waiting to finish enrollment.",
      accentClassName: "border-amber-200 bg-amber-50/80 text-amber-950",
    },
    {
      title: "Stale or offline visibility",
      count: summary.counts.stale + summary.counts.offline,
      detail:
        summary.counts.stale + summary.counts.offline > 0
          ? "Investigate stale or offline metadata visibility before trusting this hosted fleet posture as current."
          : "All linked deployments are reporting current metadata visibility.",
      accentClassName: "border-rose-200 bg-rose-50/80 text-rose-950",
    },
    {
      title: "Bounded actions blocked",
      count: summary.counts.boundedActionBlocked,
      detail:
        summary.counts.boundedActionBlocked > 0
          ? "Remote credential rotation is blocked or unavailable for these deployments."
          : "Every linked deployment currently allows the bounded hosted action scope.",
      accentClassName: "border-sky-200 bg-sky-50/80 text-sky-950",
    },
  ];

  return (
    <section className="panel px-6 py-5" aria-labelledby="fleet-posture-summary-heading">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
            Fleet posture
          </div>
          <h3
            id="fleet-posture-summary-heading"
            className="mt-2 text-balance font-[var(--font-fira-code)] text-lg font-semibold text-slate-950"
          >
            Metadata-backed hosted fleet posture
          </h3>
          <div className="mt-2 max-w-3xl space-y-1 text-sm leading-6 text-slate-600 [text-wrap:pretty]">
            <p>{reinforcement.allowedDescriptiveClaims[0]}</p>
            <p>{reinforcement.allowedDescriptiveClaims[1]}</p>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-600 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Fleet scan
          </div>
          <div className="mt-1 font-[var(--font-fira-code)] text-base font-semibold text-slate-950 [font-variant-numeric:tabular-nums]">
            {formatDeploymentCount(summary.counts.total)}
          </div>
          <p className="mt-1 max-w-xs leading-5 [text-wrap:pretty]">
            {summary.counts.total > 0
              ? reinforcement.operatorReadingGuidance[0]
              : "Create a deployment slot to start enrollment and populate hosted fleet posture."}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <article
            key={card.title}
            className={`rounded-3xl border p-4 shadow-sm transition-colors ${card.accentClassName}`}
          >
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-current/70">
              {card.title}
            </div>
            <div className="mt-3 font-[var(--font-fira-code)] text-3xl font-semibold [font-variant-numeric:tabular-nums]">
              {card.count}
            </div>
            <p className="mt-2 text-sm leading-6 text-current/80 [text-wrap:pretty]">{card.detail}</p>
          </article>
        ))}
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm leading-6 text-slate-600 shadow-sm">
          <span className="font-semibold text-slate-950">Trust boundary:</span>{" "}
          {reinforcement.operatorReadingGuidance[1]}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm leading-6 text-slate-600 shadow-sm">
          <span className="font-semibold text-slate-950">Bounded actions:</span>{" "}
          {reinforcement.boundedActionPhrasing.description}
        </div>
      </div>
    </section>
  );
}
