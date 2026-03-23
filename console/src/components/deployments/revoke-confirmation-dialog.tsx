"use client";

import { LoaderCircle } from "lucide-react";

type RevokeConfirmationDialogProps = {
  open: boolean;
  isRevoking: boolean;
  onConfirm: () => void;
  onDismiss: () => void;
};

export function RevokeConfirmationDialog({
  open,
  isRevoking,
  onConfirm,
  onDismiss,
}: RevokeConfirmationDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm">
      <div className="panel w-full max-w-md px-6 py-6">
        <h3 className="font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
          Revoke this deployment?
        </h3>
        <p className="mt-3 text-sm text-slate-600">
          The deployment&apos;s credential will be invalidated immediately. The gateway will lose
          hosted-plane access on its next heartbeat. Use Relink to restore access.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-xl bg-pink-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-pink-800 focus:outline-none focus:ring-2 focus:ring-pink-400/30 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isRevoking}
            onClick={onConfirm}
          >
            {isRevoking ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : null}
            Revoke deployment
          </button>
          <button type="button" className="secondary-button" onClick={onDismiss}>
            Keep deployment
          </button>
        </div>
      </div>
    </div>
  );
}
