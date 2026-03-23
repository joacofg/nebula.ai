"use client";

import { LoaderCircle } from "lucide-react";

type UnlinkConfirmationDialogProps = {
  open: boolean;
  isUnlinking: boolean;
  onConfirm: () => void;
  onDismiss: () => void;
};

export function UnlinkConfirmationDialog({
  open,
  isUnlinking,
  onConfirm,
  onDismiss,
}: UnlinkConfirmationDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm">
      <div className="panel w-full max-w-md px-6 py-6">
        <h3 className="font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
          Unlink this deployment?
        </h3>
        <p className="mt-3 text-sm text-slate-600">
          The gateway will stop sending heartbeats and lose hosted features. Local serving continues
          unaffected. You can relink at any time.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            className="secondary-button gap-2"
            disabled={isUnlinking}
            onClick={onConfirm}
          >
            {isUnlinking ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
            Unlink deployment
          </button>
          <button type="button" className="secondary-button" onClick={onDismiss}>
            Keep linked
          </button>
        </div>
      </div>
    </div>
  );
}
