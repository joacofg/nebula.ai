"use client";

import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";

const COPIED_RESET_MS = 2000;

type RevealApiKeyDialogProps = {
  apiKey: string | null;
  open: boolean;
  onClose: () => void;
};

export function RevealApiKeyDialog({ apiKey, open, onClose }: RevealApiKeyDialogProps) {
  const [copied, setCopied] = useState(false);

  const revealedApiKey = apiKey ?? "";
  const visible = open && apiKey !== null;

  // "Copiada" is a confirmation, not a state: it goes back to "Copiar" after a moment, and a
  // dialog that stays mounted while closed must not reopen already saying "Copiada".
  useEffect(() => {
    if (!copied) {
      return;
    }
    const timer = setTimeout(() => setCopied(false), COPIED_RESET_MS);
    return () => clearTimeout(timer);
  }, [copied]);

  useEffect(() => {
    if (!visible) {
      setCopied(false);
    }
  }, [visible]);

  async function handleCopy() {
    await navigator.clipboard.writeText(revealedApiKey);
    setCopied(true);
  }

  return (
    <Dialog open={visible} onOpenChange={(next) => (next ? null : onClose())}>
      <DialogContent
        aria-label="Clave de API"
        className="sm:max-w-xl"
        showCloseButton={false}
        onInteractOutside={(event) => event.preventDefault()}
      >
        <DialogTitle className="text-lg font-semibold text-ink">Clave de API</DialogTitle>
        <DialogDescription className="text-sm text-ink-3">No se vuelve a mostrar.</DialogDescription>

        <div className="border border-line bg-canvas px-4 py-3 font-mono text-[14px] break-all text-ink">{revealedApiKey}</div>

        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={handleCopy}>
            {copied ? <Check aria-hidden className="size-4" /> : <Copy aria-hidden className="size-4" />}
            {copied ? "Copiada" : "Copiar"}
          </Button>
          <Button type="button" variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
