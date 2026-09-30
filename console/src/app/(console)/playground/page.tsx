"use client";

import { useEffect, useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";

import Link from "next/link";

import { PageHeader } from "@/components/system/page-header";
import { EmptyState, LoadingRows } from "@/components/system/state";
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
        throw new Error("Falta la sesión de admin.");
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
    <section>
      <PageHeader
        title="Playground"
        cells={[
          { label: "Modo", value: "Sin streaming" },
          { label: "Sesión", value: "admin" },
        ]}
      />

      <div className="grid xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="border-line px-6 py-6 xl:border-r">
          {tenantsQuery.isLoading ? (
            <LoadingRows rows={4} label="Cargando tenants" />
          ) : tenantsQuery.isError ? (
            <ErrorAlert error={tenantsQuery.error} fallback="No se pudieron cargar los tenants." />
          ) : (tenantsQuery.data ?? []).length === 0 ? (
            <EmptyState
              title="No hay tenants."
              action={
                <Link href="/tenants" className="text-sm font-semibold text-ink underline underline-offset-4 hover:text-mark">
                  Crear tenant
                </Link>
              }
            />
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

        <div className="min-w-0 border-t border-line px-6 py-6 xl:border-t-0">
          <PlaygroundResponseCard result={mutation.data} error={mutation.error} adminKey={adminKey} />
        </div>
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
    return <ErrorAlert error={error} fallback="No se pudo completar el pedido." />;
  }

  if (!result) {
    return <EmptyState title="Enviar un prompt para ver la respuesta y la decisión." />;
  }

  return (
    <div className="flex flex-col gap-8">
      {result.errorDetail ? (
        <Alert variant="destructive">
          <AlertDescription>{result.errorDetail}</AlertDescription>
        </Alert>
      ) : null}
      {result.body ? <PlaygroundResponse content={result.body.choices[0]?.message.content ?? ""} /> : null}
      {recordedOutcomeQuery.isLoading ? (
        <LoadingRows rows={3} label="Esperando el registro del ledger" />
      ) : recordedOutcomeQuery.isError ? (
        <Alert variant="warning">
          <AlertDescription>
            {recordedOutcomeQuery.error instanceof Error
              ? recordedOutcomeQuery.error.message
              : "No se pudo leer el registro del ledger."}
          </AlertDescription>
        </Alert>
      ) : recordedOutcomeQuery.data ? (
        <>
          <PlaygroundDecision entry={recordedOutcomeQuery.data} routeTier={result.routeTier ?? ""} />
          <PlaygroundRecordedOutcome entry={recordedOutcomeQuery.data} />
        </>
      ) : null}
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
    </div>
  );
}
