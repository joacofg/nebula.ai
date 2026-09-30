"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
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
      <DialogContent aria-label="Clave de API" className="sm:max-w-xl" onInteractOutside={(event) => event.preventDefault()}>
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
