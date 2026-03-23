"use client";

import { useState } from "react";
import { Check, Copy, KeyRound } from "lucide-react";

import type { EnrollmentTokenResponse } from "@/lib/admin-api";

type EnrollmentTokenRevealDialogProps = {
  tokenResponse: EnrollmentTokenResponse | null;
  open: boolean;
  onClose: () => void;
};

export function EnrollmentTokenRevealDialog({
  tokenResponse,
  open,
  onClose,
}: EnrollmentTokenRevealDialogProps) {
  const [copied, setCopied] = useState(false);

  if (!open || !tokenResponse) {
    return null;
  }

  async function handleCopy() {
    if (!tokenResponse) return;
    await navigator.clipboard.writeText(tokenResponse.token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm">
      <div className="panel w-full max-w-xl px-6 py-6">
        <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-sky-50 text-sky-700">
          <KeyRound className="h-5 w-5" />
        </div>
        <h3 className="mt-4 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
          Enrollment token
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          This token will not be shown again. Copy it now and set it as{" "}
          <span className="font-[var(--font-fira-code)] text-slate-800">
            NEBULA_ENROLLMENT_TOKEN
          </span>{" "}
          in your gateway&apos;s environment, then restart the gateway.
        </p>

        <div className="mt-5 rounded-lg bg-slate-950 px-4 py-4 font-[var(--font-fira-code)] text-sm text-sky-100">
          {tokenResponse.token}
        </div>

        <div className="mt-3 rounded-lg bg-slate-950 px-4 py-4 font-[var(--font-fira-code)] text-sm text-sky-100">
          NEBULA_ENROLLMENT_TOKEN={tokenResponse.token}
        </div>

        <p className="mt-3 text-xs text-slate-500">
          Token expires in 1 hour. If it expires before use, generate a new one from this
          deployment&apos;s detail panel.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <button type="button" className="action-button gap-2" onClick={handleCopy}>
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied" : "Copy token"}
          </button>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
