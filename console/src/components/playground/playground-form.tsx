"use client";

import { LoaderCircle, SendHorizontal } from "lucide-react";

import type { TenantRecord } from "@/lib/admin-api";

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
      className="panel space-y-5 px-6 py-5"
      onSubmit={async (event) => {
        event.preventDefault();
        if (submitDisabled) {
          return;
        }
        await onSubmit();
      }}
    >
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Run prompt</div>
        <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
          Operator playground request
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          Choose the tenant context on purpose, set the target model, and send one admin-session prompt through the
          non-streaming playground path.
        </p>
      </div>

      {sessionMissing ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Operator session missing.
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
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
          <span className="field-label">Model</span>
          <input
            className="field-input"
            value={model}
            onChange={(event) => onModelChange(event.target.value)}
            disabled={disabled}
          />
        </label>
      </div>

      <label className="block">
        <span className="field-label">Prompt</span>
        <textarea
          className="field-input min-h-40 resize-y"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="Ask Nebula to summarize the current routing decision..."
          disabled={disabled}
        />
      </label>

      <div className="flex items-center justify-between gap-4">
        <p className="max-w-xl text-sm text-slate-500">
          The first response stays immediate and only shows completion content plus the request id; recorded ledger
          evidence appears after Nebula persists the outcome for that same request.
        </p>
        <button type="submit" className="action-button gap-2" disabled={submitDisabled}>
          {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <SendHorizontal className="h-4 w-4" />}
          Run prompt
        </button>
      </div>
    </form>
  );
}
