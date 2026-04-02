"use client";

import { useEffect, useMemo, useState } from "react";

import { useQuery } from "@tanstack/react-query";

import { RuntimeHealthCards } from "@/components/health/runtime-health-cards";
import { LedgerFilters } from "@/components/ledger/ledger-filters";
import { LedgerRequestDetail } from "@/components/ledger/ledger-request-detail";
import { LedgerTable } from "@/components/ledger/ledger-table";
import { getTenantRecommendations, listTenants, listUsageLedger } from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatUsd(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "N/A";
  }
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return value;
  }
  return timestamp.toLocaleString();
}

function recommendationTone(category: "policy" | "cache" | "info") {
  if (category === "policy") {
    return "border-amber-200 bg-amber-50 text-amber-950";
  }
  if (category === "cache") {
    return "border-sky-200 bg-sky-50 text-sky-950";
  }
  return "border-slate-200 bg-slate-50 text-slate-950";
}

function cacheInsightTone(level: "info" | "notice" | "warning") {
  if (level === "warning") {
    return "border-rose-200 bg-rose-50 text-rose-950";
  }
  if (level === "notice") {
    return "border-amber-200 bg-amber-50 text-amber-950";
  }
  return "border-slate-200 bg-slate-50 text-slate-900";
}

function calibrationBadgeTone(state: "sufficient" | "thin" | "stale") {
  if (state === "sufficient") {
    return "border-emerald-200 bg-emerald-50 text-emerald-900";
  }
  if (state === "stale") {
    return "border-amber-200 bg-amber-50 text-amber-950";
  }
  return "border-slate-200 bg-slate-50 text-slate-900";
}

export default function ObservabilityPage() {
  const { adminKey } = useAdminSession();
  const [tenantId, setTenantId] = useState("");
  const [routeTarget, setRouteTarget] = useState("");
  const [terminalStatus, setTerminalStatus] = useState("");
  const [fromTimestamp, setFromTimestamp] = useState("");
  const [toTimestamp, setToTimestamp] = useState("");
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);

  const tenantsQuery = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: () => listTenants(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  useEffect(() => {
    if (!tenantId && tenantsQuery.data?.length) {
      setTenantId(tenantsQuery.data[0].id);
    }
  }, [tenantId, tenantsQuery.data]);

  const ledgerFilters = {
    tenantId,
    routeTarget,
    terminalStatus,
    fromTimestamp,
    toTimestamp,
  };
  // terminal_status is encoded by the shared admin API client from this filter object.
  const ledgerQuery = useQuery({
    queryKey: queryKeys.usageLedger(ledgerFilters),
    queryFn: () => listUsageLedger(adminKey ?? "", ledgerFilters),
    enabled: Boolean(adminKey),
  });
  const runtimeHealthQuery = useQuery({
    queryKey: queryKeys.runtimeHealth,
    queryFn: async () => {
      const response = await fetch("/api/runtime/health", {
        cache: "no-store",
        headers: {
          "X-Nebula-Admin-Key": adminKey ?? "",
        },
      });
      if (!response.ok) {
        throw new Error("Unable to load runtime health.");
      }
      return (await response.json()) as {
        dependencies: Record<string, { status: string; required: boolean; detail: string }>;
      };
    },
    enabled: Boolean(adminKey),
  });

  const recommendationsQuery = useQuery({
    queryKey: queryKeys.tenantRecommendations(tenantId || "unselected"),
    queryFn: () => getTenantRecommendations(adminKey ?? "", tenantId),
    enabled: Boolean(adminKey) && tenantId.length > 0,
  });

  useEffect(() => {
    if (!selectedRequestId && ledgerQuery.data?.length) {
      setSelectedRequestId(ledgerQuery.data[0].request_id);
    }
  }, [ledgerQuery.data, selectedRequestId]);

  const selectedEntry =
    ledgerQuery.data?.find((entry) => entry.request_id === selectedRequestId) ?? ledgerQuery.data?.[0] ?? null;

  const recommendationSummary = useMemo(() => {
    const recommendationCount = recommendationsQuery.data?.recommendations.length ?? 0;
    const evaluatedRequests = recommendationsQuery.data?.window_requests_evaluated ?? 0;
    return { recommendationCount, evaluatedRequests };
  }, [recommendationsQuery.data]);

  return (
    <section className="space-y-6">
      <header className="panel px-6 py-5">
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Observability</div>
        <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
          Persisted request evidence
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Inspect the persisted usage ledger for recorded request outcomes by tenant, route target, terminal status,
          and time window so operators can confirm the final route, fallback, provider, and policy evidence behind
          each request after correlating the same request through public X-Request-ID and X-Nebula-* headers, then
          use dependency health, calibration evidence, and recommendation summaries as supporting runtime context for
          the same investigation.
        </p>
      </header>

      <LedgerFilters
        tenants={tenantsQuery.data ?? []}
        tenantId={tenantId}
        routeTarget={routeTarget}
        terminalStatus={terminalStatus}
        fromTimestamp={fromTimestamp}
        toTimestamp={toTimestamp}
        onTenantIdChange={setTenantId}
        onRouteTargetChange={setRouteTarget}
        onTerminalStatusChange={setTerminalStatus}
        onFromTimestampChange={setFromTimestamp}
        onToTimestampChange={setToTimestamp}
        onRefresh={() => {
          void ledgerQuery.refetch();
          void recommendationsQuery.refetch();
        }}
      />

      <section className="space-y-4">
        <header className="panel px-6 py-5">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
            Grounded recommendations
          </div>
          <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
            Next-best actions from recent tenant traffic
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Recommendations are derived from recent ledger-backed traffic plus supporting runtime context. They are
            bounded operator guidance, not black-box optimization, and they stay read-only until you choose to adjust
            policy controls elsewhere in the console.
          </p>
        </header>

        {recommendationsQuery.isError ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
            {recommendationsQuery.error instanceof Error
              ? recommendationsQuery.error.message
              : "Unable to load tenant recommendations."}
          </div>
        ) : recommendationsQuery.isLoading ? (
          <div className="panel px-6 py-5 text-sm text-slate-500">Loading grounded recommendations...</div>
        ) : recommendationsQuery.data ? (
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <article className="panel px-6 py-5">
                <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Recommendations</div>
                <div className="mt-3 text-2xl font-semibold text-slate-950">
                  {recommendationSummary.recommendationCount}
                </div>
                <p className="mt-2 text-sm text-slate-600">Bounded operator actions currently surfaced for this tenant.</p>
              </article>
              <article className="panel px-6 py-5">
                <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Ledger window</div>
                <div className="mt-3 text-2xl font-semibold text-slate-950">
                  {recommendationSummary.evaluatedRequests}
                </div>
                <p className="mt-2 text-sm text-slate-600">Recent ledger-backed requests evaluated for this summary.</p>
              </article>
              <article className="panel px-6 py-5">
                <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Estimated hit rate</div>
                <div className="mt-3 text-2xl font-semibold text-slate-950">
                  {formatPercent(recommendationsQuery.data.cache_summary.estimated_hit_rate)}
                </div>
                <p className="mt-2 text-sm text-slate-600">Observed cache effectiveness from recent traffic patterns.</p>
              </article>
              <article className="panel px-6 py-5">
                <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Avoided premium cost</div>
                <div className="mt-3 text-2xl font-semibold text-slate-950">
                  {formatUsd(recommendationsQuery.data.cache_summary.avoided_premium_cost_usd)}
                </div>
                <p className="mt-2 text-sm text-slate-600">Estimated premium spend avoided by semantic-cache reuse.</p>
              </article>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
              <section className="space-y-4">
                {recommendationsQuery.data.recommendations.length === 0 ? (
                  <div className="panel px-6 py-5 text-sm text-slate-600">
                    No immediate recommendation cards were derived from the current ledger window and runtime context.
                  </div>
                ) : (
                  recommendationsQuery.data.recommendations.map((recommendation) => (
                    <article
                      key={recommendation.code}
                      className={`rounded-2xl border px-6 py-5 ${recommendationTone(recommendation.category)}`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-[0.24em] opacity-80">
                            {recommendation.category} recommendation • priority {recommendation.priority}
                          </div>
                          <h3 className="mt-2 font-[var(--font-fira-code)] text-lg font-semibold">
                            {recommendation.title}
                          </h3>
                        </div>
                        <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-slate-700">
                          {recommendation.code}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-6">{recommendation.summary}</p>
                      <div className="mt-4 rounded-xl border border-white/60 bg-white/60 px-4 py-3 text-sm text-slate-800">
                        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                          Recommended action
                        </div>
                        <p className="mt-2">{recommendation.recommended_action}</p>
                      </div>
                      {recommendation.evidence.length > 0 ? (
                        <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                          {recommendation.evidence.map((item) => (
                            <div key={`${recommendation.code}-${item.label}`} className="rounded-xl bg-white/70 px-4 py-3">
                              <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                                {item.label}
                              </dt>
                              <dd className="mt-2 text-sm font-medium text-slate-900">{item.value}</dd>
                            </div>
                          ))}
                        </dl>
                      ) : null}
                    </article>
                  ))
                )}
              </section>

              <section className="space-y-4">
                <article className="panel px-6 py-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
                        Calibration evidence
                      </div>
                      <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
                        Tenant-scoped replay readiness context
                      </h3>
                    </div>
                    <span
                      className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${calibrationBadgeTone(recommendationsQuery.data.calibration_summary.state)}`}
                    >
                      {recommendationsQuery.data.calibration_summary.state}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    This summary is derived from existing ledger metadata for the selected tenant. It helps operators
                    judge whether calibration evidence is sufficient, stale, or still thin without turning Observability
                    into a replacement for the persisted request record.
                  </p>
                  <div className="mt-4 rounded-xl border border-border bg-slate-50 px-4 py-4">
                    <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">State reason</div>
                    <p className="mt-2 text-sm font-medium text-slate-950">
                      {recommendationsQuery.data.calibration_summary.state_reason}
                    </p>
                  </div>
                  <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Eligible calibrated rows
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {recommendationsQuery.data.calibration_summary.eligible_request_count}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Sufficiency threshold
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {recommendationsQuery.data.calibration_summary.thin_request_threshold}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Latest eligible row
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {formatTimestamp(recommendationsQuery.data.calibration_summary.latest_eligible_request_at)}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Rollout-disabled rows
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {recommendationsQuery.data.calibration_summary.gated_request_count}
                      </dd>
                    </div>
                  </dl>
                  <p className="mt-4 text-sm text-slate-600">
                    Keep using the ledger row and request ID correlation as the primary proof. This tenant summary only
                    explains whether replay and calibration posture are grounded by enough recent metadata-backed traffic.
                  </p>
                </article>

                <section className="panel space-y-4 px-6 py-5">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Semantic cache</div>
                    <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
                      Cache effectiveness and runtime controls
                    </h3>
                    <p className="mt-2 text-sm text-slate-600">
                      This summary shows the current runtime-enforced cache posture and the supporting evidence behind it.
                      Tune these controls in the existing policy editor; this page stays inspection-only.
                    </p>
                  </div>

                  <dl className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Cache enabled</dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {recommendationsQuery.data.cache_summary.enabled ? "Yes" : "No"}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Runtime status</dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {recommendationsQuery.data.cache_summary.runtime_status}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Similarity threshold
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {recommendationsQuery.data.cache_summary.similarity_threshold.toFixed(2)}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Max entry age
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-slate-900">
                        {recommendationsQuery.data.cache_summary.max_entry_age_hours} hours
                      </dd>
                    </div>
                  </dl>

                  <div className="rounded-xl border border-border bg-slate-50 px-4 py-3 text-sm text-slate-700">
                    <span className="font-medium text-slate-900">Runtime detail:</span>{" "}
                    {recommendationsQuery.data.cache_summary.runtime_detail}
                  </div>

                  {recommendationsQuery.data.cache_summary.insights.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500">
                      No additional cache insights were derived from the current evidence window.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {recommendationsQuery.data.cache_summary.insights.map((insight) => (
                        <article
                          key={insight.code}
                          className={`rounded-xl border px-4 py-4 ${cacheInsightTone(insight.level)}`}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <div className="text-xs font-semibold uppercase tracking-[0.2em] opacity-80">
                                {insight.level} cache insight
                              </div>
                              <h4 className="mt-2 font-[var(--font-fira-code)] text-base font-semibold">
                                {insight.title}
                              </h4>
                            </div>
                            <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-slate-700">
                              {insight.code}
                            </span>
                          </div>
                          <p className="mt-3 text-sm leading-6">{insight.summary}</p>
                          {insight.evidence.length > 0 ? (
                            <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                              {insight.evidence.map((item) => (
                                <div key={`${insight.code}-${item.label}`} className="rounded-xl bg-white/70 px-4 py-3">
                                  <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                                    {item.label}
                                  </dt>
                                  <dd className="mt-2 text-sm font-medium text-slate-900">{item.value}</dd>
                                </div>
                              ))}
                            </dl>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  )}
                </section>
              </section>
            </div>
          </div>
        ) : null}
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.8fr)]">
        {ledgerQuery.isError ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
            {ledgerQuery.error instanceof Error ? ledgerQuery.error.message : "Unable to load the usage ledger."}
          </div>
        ) : (
          <LedgerTable
            rows={ledgerQuery.data ?? []}
            selectedRequestId={selectedEntry?.request_id ?? null}
            onSelectRow={(requestId) => setSelectedRequestId(requestId)}
            isLoading={ledgerQuery.isLoading}
          />
        )}

        <LedgerRequestDetail
          entry={selectedEntry}
          calibrationSummary={recommendationsQuery.data?.calibration_summary ?? null}
        />
      </div>

      <section className="space-y-4">
        <header className="panel px-6 py-5">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Dependency health</div>
          <h2 className="mt-2 font-[var(--font-fira-code)] text-2xl font-semibold text-slate-950">
            Dependency health context
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            These dependency states do not replace the ledger record; they provide supporting runtime context for the
            same investigation. Required dependency failures block confidence immediately, while degraded optional
            dependencies stay visible here so operators can explain reduced capability without losing the persisted
            request trail.
          </p>
        </header>

        {runtimeHealthQuery.isError ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-sm text-rose-900">
            {runtimeHealthQuery.error instanceof Error
              ? runtimeHealthQuery.error.message
              : "Unable to load dependency health."}
          </div>
        ) : (
          <RuntimeHealthCards
            dependencies={runtimeHealthQuery.data?.dependencies ?? {}}
            isLoading={runtimeHealthQuery.isLoading}
          />
        )}
      </section>
    </section>
  );
}
