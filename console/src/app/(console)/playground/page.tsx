"use client";

import { useEffect, useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";
import { FlaskConical, LoaderCircle } from "lucide-react";

import { PlaygroundDecision } from "@/components/playground/playground-decision";
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
import { ErrorAlert } from "@/components/system/state";
import { Alert, AlertDescription } from "@/components/ui/alert";

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
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Playground</div>
            <h2 className="mt-2 font-(--font-fira-code) text-2xl font-semibold text-ink">
              Operator corroboration sandbox
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-ink-3">
              Use the active admin session to run a non-streaming corroboration request for the tenant you select here.
              This checks the live Nebula routing path without acting as the public <code>POST /v1/chat/completions</code>{" "}
              integration boundary.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-mark-soft px-3 py-1 text-xs font-semibold text-mark">
            <FlaskConical className="h-3.5 w-3.5" />
            Non-streaming
          </div>
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
        <div className="space-y-4">
          {tenantsQuery.isLoading ? (
            <div className="panel flex items-center gap-3 px-6 py-5 text-sm text-ink-4">
              <LoaderCircle className="h-4 w-4 animate-spin" />
              Loading tenant inventory...
            </div>
          ) : tenantsQuery.isError ? (
            <ErrorAlert error={tenantsQuery.error} fallback="Unable to load tenants." />
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
      <ErrorAlert error={error} fallback="Unable to complete the request." />
    );
  }

  if (!result) {
    return (
      <div className="panel px-6 py-5 text-sm text-ink-4">
        Submit a prompt to see the assistant response, routing evidence, and request correlation id.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {result.errorDetail ? (
        <Alert variant="destructive">
          <AlertDescription>{result.errorDetail}</AlertDescription>
        </Alert>
      ) : null}
      {result.body ? <PlaygroundResponse content={result.body.choices[0]?.message.content ?? ""} /> : null}
      <PlaygroundMetadata
        requestId={result.requestId}
        tenantId={result.tenantId}
        routeTarget={result.routeTarget}
        routeReason={result.routeReason}
        routeTier={result.routeTier ?? ""}
        provider={result.provider}
        cacheHit={result.cacheHit}
        fallbackUsed={result.fallbackUsed}
        latencyMs={result.latencyMs}
        policyMode={result.policyMode}
        policyOutcome={result.policyOutcome}
      />
      {recordedOutcomeQuery.isLoading ? (
        <div className="panel px-6 py-5 text-sm text-ink-4">Loading recorded outcome...</div>
      ) : recordedOutcomeQuery.isError ? (
        <Alert variant="warning">
          <AlertDescription>
            {recordedOutcomeQuery.error instanceof Error
              ? recordedOutcomeQuery.error.message
              : "Unable to load recorded outcome."}
          </AlertDescription>
        </Alert>
      ) : recordedOutcomeQuery.data ? (
        <>
          <PlaygroundDecision entry={recordedOutcomeQuery.data} routeTier={result.routeTier ?? ""} />
          <PlaygroundRecordedOutcome entry={recordedOutcomeQuery.data} />
        </>
      ) : null}
    </div>
  );
}
