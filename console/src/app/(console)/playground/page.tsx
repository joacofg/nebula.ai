"use client";

import { useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";

import Link from "next/link";

import { PageHeader } from "@/components/system/page-header";
import { EmptyState, ErrorAlert, errorMessage, LoadingRows } from "@/components/system/state";
import { PlaygroundDecision } from "@/components/playground/playground-decision";
import { PlaygroundForm } from "@/components/playground/playground-form";
import { PlaygroundMetadata, type ResponseFacts } from "@/components/playground/playground-metadata";
import { PlaygroundRecordedOutcome } from "@/components/playground/playground-recorded-outcome";
import { PlaygroundResponse } from "@/components/playground/playground-response";
import { routingModeLabel } from "@/components/system/labels";
import {
  createPlaygroundCompletion,
  getTenantPolicy,
  getUsageLedgerEntry,
  listTenants,
  type PlaygroundInput,
  type PlaygroundCompletionResult,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
import { formatTarget } from "@/lib/quality-target";
import { useSelectedTenant } from "@/lib/selected-tenant";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function PlaygroundPage() {
  const { adminKey } = useAdminSession();
  const [model, setModel] = useState("nebula-auto");
  const [prompt, setPrompt] = useState("");

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const { tenantId, tenant, setTenantId } = useSelectedTenant(tenantsQuery.data);
  const selectedTenantId = tenantId ?? "";

  // The header's target and mode come from the tenant's policy, the query the Política page shares.
  const policyQuery = useQuery({
    queryKey: queryKeys.tenantPolicy(selectedTenantId || "unselected"),
    queryFn: () => getTenantPolicy(adminKey ?? "", selectedTenantId),
    enabled: Boolean(adminKey) && selectedTenantId.length > 0,
  });
  const policy = policyQuery.data;

  const mutation = useMutation({
    mutationFn: async (payload: PlaygroundInput) => {
      if (!adminKey) {
        throw new Error("Falta la sesión de admin.");
      }
      return createPlaygroundCompletion(adminKey, payload);
    },
  });

  const sessionMissing = !adminKey;

  return (
    <section>
      <PageHeader
        title="Playground"
        cells={[
          { label: "Tenant", value: tenant?.name ?? "—" },
          {
            label: "Objetivo",
            value: typeof policy?.routing_quality_target === "number" ? formatTarget(policy.routing_quality_target) : "—",
          },
          { label: "Modo de ruteo", value: policy ? routingModeLabel(policy.routing_mode_default) : "—" },
        ]}
      />

      <div className="grid xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="border-line px-6 py-6 xl:border-r">
          {/* `isPending`, not `isLoading`: a list paused while the gateway is unreachable is still waiting. */}
          {tenantsQuery.isPending ? (
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
              onSelectedTenantIdChange={setTenantId}
              onModelChange={setModel}
              onPromptChange={setPrompt}
              // `mutate` never rejects: a request that cannot be sent lands in `mutation.error`,
              // which the result card shows.
              onSubmit={() => mutation.mutate({ tenantId: selectedTenantId, model, prompt })}
            />
          )}
        </div>

        <div className="min-w-0 border-t border-line px-6 py-6 xl:border-t-0">
          <PlaygroundResponseCard
            result={mutation.data}
            error={mutation.error}
            isPending={mutation.isPending}
            adminKey={adminKey}
          />
        </div>
      </div>
    </section>
  );
}

function responseFacts(result: PlaygroundCompletionResult): ResponseFacts {
  return {
    routeTarget: result.routeTarget,
    routeReason: result.routeReason,
    routeTier: result.routeTier ?? "",
    provider: result.provider,
    cacheHit: result.cacheHit,
    fallbackUsed: result.fallbackUsed,
  };
}

function PlaygroundResponseCard({
  result,
  error,
  isPending,
  adminKey,
}: {
  result: PlaygroundCompletionResult | undefined;
  error: Error | null;
  isPending: boolean;
  adminKey: string | null;
}) {
  const requestId = result?.requestId ?? "";
  const lookupEnabled = Boolean(adminKey && requestId);
  const recordedOutcomeQuery = useQuery({
    queryKey: queryKeys.usageLedgerEntry(requestId),
    queryFn: async () => {
      if (!adminKey) {
        return null;
      }
      return getUsageLedgerEntry(adminKey, requestId);
    },
    enabled: lookupEnabled,
  });
  // `isPending`, not `isLoading`: a lookup paused while the gateway is unreachable is still waiting.
  // A disabled one (no request yet) is pending forever, so it only counts once it can run.
  const waitingForLedger = lookupEnabled && recordedOutcomeQuery.isPending;

  // TanStack clears `data` and `error` when a request starts, so a pending one has neither. The
  // waiting rows say it once, as the other loading states do.
  if (isPending) {
    return <LoadingRows rows={4} label="Esperando respuesta…" />;
  }

  if (error) {
    return <ErrorAlert error={error} fallback="No se pudo completar el pedido." />;
  }

  if (!result) {
    return <EmptyState title="Enviar un prompt para ver la respuesta y la decisión." />;
  }

  return (
    <div className="flex flex-col gap-8">
      {result.errorDetail ? <ErrorAlert error={result.errorDetail} fallback="No se pudo completar el pedido." /> : null}
      {result.body ? <PlaygroundResponse content={result.body.choices[0]?.message.content ?? ""} /> : null}
      {waitingForLedger ? (
        <LoadingRows rows={3} label="Esperando el registro del ledger" />
      ) : recordedOutcomeQuery.isError ? (
        <Alert variant="warning">
          <AlertDescription>
            {errorMessage(recordedOutcomeQuery.error, "No se pudo leer el registro del ledger.")}
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
        policyMode={result.policyMode}
        policyOutcome={result.policyOutcome}
        // The ledger block records the routing facts once. Without a ledger record (the lookup
        // failed, or found nothing) the headers' copy keeps the result from coming back empty;
        // while the lookup runs it waits, so the facts never show in both places.
        response={recordedOutcomeQuery.data || waitingForLedger ? undefined : responseFacts(result)}
      />
    </div>
  );
}
