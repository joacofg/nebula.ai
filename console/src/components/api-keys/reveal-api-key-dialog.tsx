"use client";

import { useEffect, useRef, useState } from "react";
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

  // The key on screen right now; a copy only confirms itself if it is still the one being shown
  // when the clipboard answers.
  const shownKeyRef = useRef<string | null>(null);
  useEffect(() => {
    shownKeyRef.current = visible ? apiKey : null;
    return () => {
      shownKeyRef.current = null;
    };
  }, [visible, apiKey]);

  async function handleCopy() {
    const key = revealedApiKey;
    try {
      await navigator.clipboard.writeText(key);
    } catch {
      // No clipboard API (plain HTTP on a LAN) or the browser refused: stay on "Copiar", and the
      // key remains on screen to select by hand.
      return;
    }
    if (shownKeyRef.current === key) {
      setCopied(true);
    }
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
