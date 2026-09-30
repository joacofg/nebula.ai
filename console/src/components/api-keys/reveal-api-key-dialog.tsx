"use client";

import { useState } from "react";
import { Check, Copy, KeyRound } from "lucide-react";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";

type RevealApiKeyDialogProps = {
  apiKey: string | null;
  open: boolean;
  onClose: () => void;
};

export function RevealApiKeyDialog({ apiKey, open, onClose }: RevealApiKeyDialogProps) {
  const [copied, setCopied] = useState(false);

  const revealedApiKey = apiKey ?? "";

  async function handleCopy() {
    await navigator.clipboard.writeText(revealedApiKey);
    setCopied(true);
  }

  return (
    <Dialog open={open && apiKey !== null} onOpenChange={(next) => (next ? null : onClose())}>
      <DialogContent aria-label="Raw API key" className="sm:max-w-xl">
        <div className="inline-flex h-11 w-11 items-center justify-center bg-mark-soft text-mark">
          <KeyRound className="h-5 w-5" />
        </div>
        <DialogTitle className="text-xl font-semibold text-ink">Raw API key</DialogTitle>
        <DialogDescription className="text-sm text-ink-3">This key will not be shown again.</DialogDescription>

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
      </DialogContent>
    </Dialog>
  );
}
