import type { DependencySummary } from "@/lib/admin-api";

type DependencyHealthPillsProps = {
  summary: DependencySummary | null;
};

const STATUS_DOT: Record<string, string> = {
  healthy: "bg-emerald-500",
  degraded: "bg-amber-500",
  unavailable: "bg-rose-500",
};

type PillEntry = { name: string; status: string };

function toPills(summary: DependencySummary): PillEntry[] {
  const pills: PillEntry[] = [];
  for (const name of summary.healthy) {
    pills.push({ name, status: "healthy" });
  }
  for (const name of summary.degraded) {
    pills.push({ name, status: "degraded" });
  }
  for (const name of summary.unavailable) {
    pills.push({ name, status: "unavailable" });
  }
  return pills;
}

export function DependencyHealthPills({ summary }: DependencyHealthPillsProps) {
  if (summary === null) {
    return <span className="text-sm text-slate-400">No data reported</span>;
  }

  const pills = toPills(summary);
  if (pills.length === 0) {
    return <span className="text-sm text-slate-400">No data reported</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {pills.map((pill) => (
        <span
          key={pill.name}
          className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600"
        >
          <span
            className={[
              "h-2 w-2 flex-shrink-0 rounded-full",
              STATUS_DOT[pill.status] ?? STATUS_DOT.unavailable,
            ].join(" ")}
          />
          {pill.name}
        </span>
      ))}
    </div>
  );
}
