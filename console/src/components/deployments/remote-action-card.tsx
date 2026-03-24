"use client";

import { useEffect, useState } from "react";

import {
  listRemoteActions,
  queueRotateDeploymentCredential,
  type DeploymentRecord,
  type RemoteActionRecord,
  type RemoteActionStatus,
} from "@/lib/admin-api";
import { getBoundedActionAvailability } from "@/components/deployments/fleet-posture";
import { getHostedContractContent } from "@/lib/hosted-contract";
import { useAdminSession } from "@/lib/admin-session-provider";

const historyTimestampFormatter = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const STATUS_STYLES: Record<RemoteActionStatus, string> = {
  queued: "bg-amber-50 text-amber-700 border-amber-200",
  in_progress: "bg-sky-50 text-sky-700 border-sky-200",
  applied: "bg-emerald-50 text-emerald-700 border-emerald-200",
  failed: "bg-rose-50 text-rose-700 border-rose-200",
};

type RemoteActionCardProps = {
  deployment: DeploymentRecord;
};

function formatStatusLabel(status: RemoteActionStatus) {
  return status.replace("_", " ");
}

function formatTimestamp(value: string | null) {
  if (!value) return null;
  return historyTimestampFormatter.format(new Date(value));
}

export function RemoteActionCard({ deployment }: RemoteActionCardProps) {
  const { adminKey } = useAdminSession();
  const { reinforcement } = getHostedContractContent();
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<RemoteActionRecord[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { disabledReason } = getBoundedActionAvailability(deployment);

  useEffect(() => {
    if (!adminKey) {
      setHistory([]);
      return;
    }

    const activeAdminKey = adminKey;
    let cancelled = false;

    async function loadHistory() {
      setIsLoadingHistory(true);
      try {
        const rows = await listRemoteActions(activeAdminKey, deployment.id);
        if (!cancelled) {
          setHistory(rows);
        }
      } catch {
        if (!cancelled) {
          setError("Could not load remote action history.");
        }
      } finally {
        if (!cancelled) {
          setIsLoadingHistory(false);
        }
      }
    }

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [adminKey, deployment.id]);

  async function handleQueue() {
    const trimmedNote = note.trim();
    if (trimmedNote.length < 1 || trimmedNote.length > 280) {
      setError("Enter a note between 1 and 280 characters.");
      return;
    }
    if (!adminKey) {
      setError("Missing Nebula admin session.");
      return;
    }
    if (disabledReason) {
      setError(disabledReason);
      return;
    }
    if (
      !window.confirm(
        "Queue a hosted-link credential rotation for this deployment?",
      )
    ) {
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const queued = await queueRotateDeploymentCredential(adminKey, deployment.id, trimmedNote);
      setHistory((current) => [queued, ...current.filter((row) => row.id !== queued.id)]);
      setNote("");
    } catch (queueError) {
      setError(queueError instanceof Error ? queueError.message : "Could not queue rotation.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="mt-6 border-t border-border/50 pt-4">
      <div className="rounded-3xl border border-slate-200 bg-white/80 p-4 shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          Remote action
        </div>
        <h4 className="mt-2 text-lg font-semibold text-slate-950">Rotate hosted-link credential</h4>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          {reinforcement.boundedActionPhrasing.description}
        </p>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Hosted summaries here are metadata-backed and descriptive only. Use local runtime
          observability to confirm serving-time behavior before treating this deployment as healthy.
        </p>

        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-3">
          <label
            className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500"
            htmlFor={`remote-action-note-${deployment.id}`}
          >
            Rotation note
          </label>
          <textarea
            id={`remote-action-note-${deployment.id}`}
            className="mt-2 min-h-24 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-300 focus:ring-2 focus:ring-sky-200/40 disabled:bg-slate-100"
            maxLength={280}
            placeholder="Explain why this credential rotation is needed."
            value={note}
            onChange={(event) => {
              setNote(event.target.value);
              if (error === "Enter a note between 1 and 280 characters.") {
                setError(null);
              }
            }}
            disabled={Boolean(disabledReason) || isSubmitting}
          />
          <div className="mt-2 flex items-center justify-between gap-3 text-xs text-slate-500">
            <span>Required, 1-280 characters.</span>
            <span>{note.trim().length}/280</span>
          </div>
        </div>

        {disabledReason ? <p className="mt-3 text-sm text-rose-700">{disabledReason}</p> : null}
        {error ? <p className="mt-3 text-sm text-rose-700">{error}</p> : null}

        <button
          type="button"
          className="action-button mt-4"
          onClick={() => {
            void handleQueue();
          }}
          disabled={Boolean(disabledReason) || isSubmitting}
        >
          {isSubmitting ? "Queueing..." : "Queue rotation"}
        </button>

        <div className="mt-6">
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Recent history
          </div>
          {isLoadingHistory ? (
            <p className="mt-2 text-sm text-slate-500">Loading remote action history...</p>
          ) : history.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">No remote actions recorded yet.</p>
          ) : (
            <div className="mt-3 space-y-3">
              {history.map((action) => (
                <article
                  key={action.id}
                  className="rounded-2xl border border-slate-200 bg-slate-50/70 p-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span
                      className={[
                        "inline-flex items-center rounded-full border px-2 py-1 text-xs font-semibold capitalize",
                        STATUS_STYLES[action.status],
                      ].join(" ")}
                    >
                      {formatStatusLabel(action.status)}
                    </span>
                    <span className="font-[var(--font-fira-code)] text-xs text-slate-500">
                      {formatTimestamp(action.finished_at ?? action.requested_at)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-700">{action.note}</p>
                  <div className="mt-2 space-y-1 text-xs text-slate-500">
                    <div>Requested: {formatTimestamp(action.requested_at)}</div>
                    {action.finished_at ? <div>Finished: {formatTimestamp(action.finished_at)}</div> : null}
                    {action.failure_reason ? <div>Failure reason: {action.failure_reason}</div> : null}
                    {action.failure_detail ? <div>Failure detail: {action.failure_detail}</div> : null}
                    {action.result_credential_prefix ? (
                      <div>Credential prefix: {action.result_credential_prefix}</div>
                    ) : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
