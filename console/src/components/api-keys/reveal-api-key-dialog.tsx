"use client";

import { useState } from "react";
import { Check, Copy, KeyRound } from "lucide-react";

import { useDialogDismiss } from "@/lib/use-dialog-dismiss";

type RevealApiKeyDialogProps = {
  apiKey: string | null;
  open: boolean;
  onClose: () => void;
};

export function RevealApiKeyDialog({ apiKey, open, onClose }: RevealApiKeyDialogProps) {
  const [copied, setCopied] = useState(false);

  useDialogDismiss(open, onClose);

  if (!open || !apiKey) {
    return null;
  }

  const revealedApiKey = apiKey;

  async function handleCopy() {
    await navigator.clipboard.writeText(revealedApiKey);
    setCopied(true);
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-ink/45 px-4 py-6 backdrop-blur-xs">
      <div role="dialog" aria-modal="true" aria-label="Raw API key" className="panel w-full max-w-xl px-6 py-6">
        <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-mark-soft text-mark">
          <KeyRound className="h-5 w-5" />
        </div>
        <h3 className="mt-4 font-(--font-fira-code) text-xl font-semibold text-ink">
          Raw API key
        </h3>
        <p className="mt-2 text-sm text-ink-3">
          This key will not be shown again.
        </p>

        <div className="mt-5 rounded-2xl border border-line bg-ink px-4 py-4 font-(--font-fira-code) text-sm text-mark-soft">
          {revealedApiKey}
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button type="button" className="action-button gap-2" onClick={handleCopy}>
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied" : "Copy key"}
          </button>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
