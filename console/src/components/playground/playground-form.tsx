"use client";

import { LoaderCircle, SendHorizontal } from "lucide-react";

import type { TenantRecord } from "@/lib/admin-api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

/** The three runbook prompts: one per tier at the demo's quality target. */
export const EXAMPLE_PROMPTS = [
  { label: "Capital de Australia", prompt: "¿Cuál es la capital de Australia?" },
  { label: "Boletos de avión", prompt: "¿Por qué los boletos de avión están tan caros ahora?" },
  {
    label: "Criba de Eratóstenes",
    prompt: "Escribe una función en Python que devuelva los primos menores que n con la criba de Eratóstenes, con tests.",
  },
];

type PlaygroundFormProps = {
  tenants: TenantRecord[];
  selectedTenantId: string;
  model: string;
  prompt: string;
  disabled: boolean;
  isSubmitting: boolean;
  sessionMissing: boolean;
  onSelectedTenantIdChange: (tenantId: string) => void;
  onModelChange: (model: string) => void;
  onPromptChange: (prompt: string) => void;
  onSubmit: () => Promise<void>;
};

export function PlaygroundForm({
  tenants,
  selectedTenantId,
  model,
  prompt,
  disabled,
  isSubmitting,
  sessionMissing,
  onSelectedTenantIdChange,
  onModelChange,
  onPromptChange,
  onSubmit,
}: PlaygroundFormProps) {
  const submitDisabled = disabled || prompt.trim().length === 0 || selectedTenantId.length === 0;

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={async (event) => {
        event.preventDefault();
        if (submitDisabled) {
          return;
        }
        await onSubmit();
      }}
    >
      {sessionMissing ? (
        <Alert variant="warning">
          <AlertDescription>Falta la sesión de admin.</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <label>
          <span className="field-label">Tenant</span>
          <select
            className="field-input"
            value={selectedTenantId}
            onChange={(event) => onSelectedTenantIdChange(event.target.value)}
            disabled={disabled}
          >
            {tenants.map((tenant) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span className="field-label">Modelo</span>
          <input
            className="field-input font-mono text-[14px]"
            value={model}
            onChange={(event) => onModelChange(event.target.value)}
            disabled={disabled}
          />
        </label>
      </div>

      <label className="block">
        <span className="field-label">Prompt</span>
        <textarea
          className="field-input min-h-44 resize-y leading-relaxed"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          disabled={disabled}
        />
      </label>

      <div className="flex flex-wrap items-center gap-2">
        <span className="font-label text-[13px] font-medium text-ink-3">Ejemplos</span>
        {EXAMPLE_PROMPTS.map((example) => (
          <button
            key={example.label}
            type="button"
            disabled={disabled}
            onClick={() => onPromptChange(example.prompt)}
            className="h-8 border border-line bg-surface px-3 text-sm font-medium text-ink-2 transition-colors hover:border-ink hover:text-ink disabled:opacity-50"
          >
            {example.label}
          </button>
        ))}
      </div>

      <div className="flex justify-end">
        <Button type="submit" size="lg" disabled={submitDisabled}>
          {isSubmitting ? <LoaderCircle aria-hidden className="size-4 animate-spin" /> : <SendHorizontal aria-hidden className="size-4" />}
          {isSubmitting ? "Enviando…" : "Enviar"}
        </Button>
      </div>
    </form>
  );
}
