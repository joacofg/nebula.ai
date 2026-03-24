"use client";

import { useEffect, useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";
import { FlaskConical, LoaderCircle } from "lucide-react";

import { PlaygroundForm } from "@/components/playground/playground-form";
import { PlaygroundMetadata } from "@/components/playground/playground-metadata";
import { PlaygroundRecordedOutcome } from "@/components/playground/playground-recorded-outcome";
import { PlaygroundResponse } from "@/components/playground/playground-response";
import {
  createPlaygroundCompletion,
  getUsageLedgerEntry,
  listTenants,
  type PlaygroundInput,
  type PlaygroundCompletionResult,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";

export default function PlaygroundPage() {
  const { adminKey } = useAdminSession();
  const [selectedTenantId, setSelectedTenantId] = useState("");
  const [model, setModel] = useState("nebula-auto");
  const [prompt, setPrompt] = useState("");

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  useEffect(() => {
    if (!selectedTenantId && tenantsQuery.data?.length) {
      setSelectedTenantId(tenantsQuery.data[0].id);
    }
  }, [selectedTenantId, tenantsQuery.data]);

  const mutation = useMutation({
    mutationFn: async (payload: PlaygroundInput) => {
      if (!adminKey) {
        throw new Error("Operator session missing.");
      }
      const startedAt = performance.now();
      const result = await createPlaygroundCompletion(adminKey, payload);
      return {
        ...result,
        latencyMs: Math.round(performance.now() - startedAt),
      };
    },
  });

  const sessionMissing = !adminKey;

  return (
    <section className="space-y-6">
      <header className="panel px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Playground</div>
            <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
              Prompt routing sandbox
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Run prompt requests through the live Nebula routing path with the active operator session.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
            <FlaskConical className="h-3.5 w-3.5" />
            Non-streaming
          </div>
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        <div className="space-y-4">
          {tenantsQuery.isLoading ? (
            <div className="panel flex items-center gap-3 px-6 py-5 text-sm text-slate-500">
              <LoaderCircle className="h-4 w-4 animate-spin" />
              Loading tenant inventory...
            </div>
          ) : tenantsQuery.isError ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
              {tenantsQuery.error instanceof Error ? tenantsQuery.error.message : "Unable to load tenants."}
            </div>
          ) : (
            <PlaygroundForm
              tenants={tenantsQuery.data ?? []}
              selectedTenantId={selectedTenantId}
              model={model}
              prompt={prompt}
              disabled={sessionMissing || mutation.isPending || (tenantsQuery.data ?? []).length === 0}
              isSubmitting={mutation.isPending}
              sessionMissing={sessionMissing}
              onSelectedTenantIdChange={setSelectedTenantId}
              onModelChange={setModel}
              onPromptChange={setPrompt}
              onSubmit={async () => {
                await mutation.mutateAsync({
                  tenantId: selectedTenantId,
                  model,
                  prompt,
                });
              }}
            />
          )}
        </div>

        <PlaygroundResponseCard result={mutation.data} error={mutation.error} adminKey={adminKey} />
      </div>
    </section>
  );
}

function PlaygroundResponseCard({
  result,
  error,
  adminKey,
}: {
  result:
    | (PlaygroundCompletionResult & {
        latencyMs: number;
      })
    | undefined;
  error: Error | null;
  adminKey: string | null;
}) {
  const requestId = result?.requestId ?? "";
  const recordedOutcomeQuery = useQuery({
    queryKey: queryKeys.usageLedgerEntry(requestId),
    queryFn: async () => {
      if (!adminKey) {
        return null;
      }
      return getUsageLedgerEntry(adminKey, requestId);
    },
    enabled: Boolean(adminKey && requestId),
  });

  if (error) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
        {error.message}
      </div>
    );
  }

  if (!result) {
    return (
      <div className="panel px-6 py-5 text-sm text-slate-500">
        Submit a prompt to see the assistant response, routing evidence, and request correlation id.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {result.errorDetail ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
          {result.errorDetail}
        </div>
      ) : null}
      {result.body ? <PlaygroundResponse content={result.body.choices[0]?.message.content ?? ""} /> : null}
      <PlaygroundMetadata
        requestId={result.requestId}
        tenantId={result.tenantId}
        routeTarget={result.routeTarget}
        routeReason={result.routeReason}
        provider={result.provider}
        cacheHit={result.cacheHit}
        fallbackUsed={result.fallbackUsed}
        latencyMs={result.latencyMs}
        policyMode={result.policyMode}
        policyOutcome={result.policyOutcome}
      />
      {recordedOutcomeQuery.isLoading ? (
        <div className="panel px-6 py-5 text-sm text-slate-500">Loading recorded outcome...</div>
      ) : recordedOutcomeQuery.isError ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-6 py-5 text-sm text-amber-900">
          {recordedOutcomeQuery.error instanceof Error
            ? recordedOutcomeQuery.error.message
            : "Unable to load recorded outcome."}
        </div>
      ) : recordedOutcomeQuery.data ? (
        <PlaygroundRecordedOutcome entry={recordedOutcomeQuery.data} />
      ) : null}
    </div>
  );
}
