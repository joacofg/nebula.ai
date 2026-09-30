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
import { ErrorAlert } from "@/components/system/state";

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
    return "border-warn-line bg-warn-soft text-warn";
  }
  if (category === "cache") {
    return "border-mark-line bg-mark-soft text-mark";
  }
  return "border-line bg-canvas text-ink";
}

function cacheInsightTone(level: "info" | "notice" | "warning") {
  if (level === "warning") {
    return "border-danger-line bg-danger-soft text-danger";
  }
  if (level === "notice") {
    return "border-warn-line bg-warn-soft text-warn";
  }
  return "border-line bg-canvas text-ink";
}

function calibrationBadgeTone(state: "sufficient" | "thin" | "stale" | "degraded") {
  if (state === "sufficient") {
    return "border-ok-line bg-ok-soft text-ok";
  }
  if (state === "stale") {
    return "border-warn-line bg-warn-soft text-warn";
  }
  return "border-line bg-canvas text-ink";
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
        dependencies: Record<string, import("@/lib/admin-api").RuntimeHealthDependency>;
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
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Observability</div>
        <h2 className="mt-2 text-2xl font-semibold text-ink">
          Selected request evidence first
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-ink-3">
          Start with one persisted ledger row for the selected request ID so operators can confirm the final route,
          fallback, provider, routing inspection, and policy evidence behind the same request first corroborated
          through public X-Request-ID and X-Nebula-* headers. Calibration readiness, grounded recommendations,
          cache posture, and dependency health stay on this page as supporting runtime context for that same routed
          request investigation.
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
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Selected request</div>
          <h2 className="mt-2 text-2xl font-semibold text-ink">
            Inspect one persisted ledger row before reading tenant context
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-ink-3">
            Pick the request first. The selected ledger row remains the authoritative persisted record for route,
            provider, fallback, calibration state, and policy outcome. The cards below help explain the same
            investigation, but they do not overrule the selected request evidence.
          </p>
        </header>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.8fr)]">
          {ledgerQuery.isError ? (
            <ErrorAlert error={ledgerQuery.error} fallback="Unable to load the usage ledger." />
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
      </section>

      <section className="space-y-4">
        <header className="panel px-6 py-5">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Next operator step</div>
          <h2 className="mt-2 text-2xl font-semibold text-ink">
            Follow-up context for the selected request
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-ink-3">
            After the persisted request row is clear, use these supporting cards to decide the next operator action.
            Recommendations, calibration, cache posture, and dependency health stay subordinate to the selected
            request and point toward policy preview as the comparison surface before any save elsewhere in the console.
          </p>
        </header>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <section className="space-y-4" aria-labelledby="selected-request-follow-up-heading">
            <article className="panel px-6 py-5">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Follow-up guidance</div>
              <h3
                id="selected-request-follow-up-heading"
                className="mt-2 font-mono text-xl font-semibold text-ink"
              >
                Grounded follow-up guidance for the selected request
              </h3>
              <p className="mt-2 max-w-3xl text-sm text-ink-3">
                Recommendations are derived from recent ledger-backed traffic plus supporting runtime context. They stay
                bounded operator guidance for the selected-request investigation, point operators back toward the next
                comparison or follow-up action, and do not replace the persisted ledger row. Compare options in policy
                preview before saving any change elsewhere in the console.
              </p>
            </article>

            {recommendationsQuery.isError ? (
              <ErrorAlert error={recommendationsQuery.error} fallback="Unable to load tenant recommendations." />
            ) : recommendationsQuery.isLoading ? (
              <div className="panel px-6 py-5 text-sm text-ink-4">Loading grounded recommendations...</div>
            ) : recommendationsQuery.data ? (
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <article className="panel px-6 py-5">
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Recommendations</div>
                    <div className="mt-3 text-2xl font-semibold text-ink">
                      {recommendationSummary.recommendationCount}
                    </div>
                    <p className="mt-2 text-sm text-ink-3">Bounded operator actions currently surfaced for this tenant.</p>
                  </article>
                  <article className="panel px-6 py-5">
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Ledger window</div>
                    <div className="mt-3 text-2xl font-semibold text-ink">
                      {recommendationSummary.evaluatedRequests}
                    </div>
                    <p className="mt-2 text-sm text-ink-3">Recent ledger-backed requests evaluated for this summary.</p>
                  </article>
                  <article className="panel px-6 py-5">
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Estimated hit rate</div>
                    <div className="mt-3 text-2xl font-semibold text-ink">
                      {formatPercent(recommendationsQuery.data.cache_summary.estimated_hit_rate)}
                    </div>
                    <p className="mt-2 text-sm text-ink-3">Observed cache effectiveness from recent traffic patterns.</p>
                  </article>
                  <article className="panel px-6 py-5">
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Avoided premium cost</div>
                    <div className="mt-3 text-2xl font-semibold text-ink">
                      {formatUsd(recommendationsQuery.data.cache_summary.avoided_premium_cost_usd)}
                    </div>
                    <p className="mt-2 text-sm text-ink-3">Estimated premium spend avoided by semantic-cache reuse.</p>
                  </article>
                </div>

                {recommendationsQuery.data.recommendations.length === 0 ? (
                  <div className="panel px-6 py-5 text-sm text-ink-3">
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
                          <h4 className="mt-2 text-lg font-semibold">
                            {recommendation.title}
                          </h4>
                        </div>
                        <span className="rounded-full bg-surface/70 px-3 py-1 text-xs font-semibold text-ink-2">
                          {recommendation.code}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-6">{recommendation.summary}</p>
                      <div className="mt-4 rounded-xl border border-surface/60 bg-surface/60 px-4 py-3 text-sm text-ink-2">
                        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                          Recommended action
                        </div>
                        <p className="mt-2">{recommendation.recommended_action}</p>
                      </div>
                      {recommendation.evidence.length > 0 ? (
                        <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                          {recommendation.evidence.map((item) => (
                            <div key={`${recommendation.code}-${item.label}`} className="rounded-xl bg-surface/70 px-4 py-3">
                              <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                                {item.label}
                              </dt>
                              <dd className="mt-2 text-sm font-medium text-ink">{item.value}</dd>
                            </div>
                          ))}
                        </dl>
                      ) : null}
                    </article>
                  ))
                )}
              </div>
            ) : null}
          </section>

          <section className="space-y-4" aria-labelledby="policy-preview-follow-up-heading">
            <article className="panel px-6 py-5">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Next comparison</div>
              <h3
                id="policy-preview-follow-up-heading"
                className="mt-2 font-mono text-xl font-semibold text-ink"
              >
                Policy preview follow-up for the same request
              </h3>
              <p className="mt-2 text-sm text-ink-3">
                Use calibration, cache, and dependency context to judge whether a policy preview comparison is grounded
                enough for this same selected request. This page stays inspection-only: preview before saving in the
                policy editor, and keep the persisted request row as the authoritative evidence seam.
              </p>
            </article>

            {recommendationsQuery.data ? (
              <>
                <article className="panel px-6 py-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">
                        Calibration evidence
                      </div>
                      <h3 className="mt-2 text-xl font-semibold text-ink">
                        Tenant-scoped replay readiness context
                      </h3>
                    </div>
                    <span
                      className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${calibrationBadgeTone(recommendationsQuery.data.calibration_summary.state)}`}
                    >
                      {recommendationsQuery.data.calibration_summary.state}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-ink-3">
                    This summary is derived from existing ledger metadata for the selected tenant. It helps operators
                    judge whether calibration evidence is sufficient, stale, or still thin before deciding whether a
                    replay or policy preview comparison is grounded enough, without turning Observability into a
                    replacement for the persisted request record.
                  </p>
                  <div className="mt-4 rounded-xl border border-line bg-canvas px-4 py-4">
                    <div className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">State reason</div>
                    <p className="mt-2 text-sm font-medium text-ink">
                      {recommendationsQuery.data.calibration_summary.state_reason}
                    </p>
                  </div>
                  <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                        Eligible calibrated rows
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {recommendationsQuery.data.calibration_summary.eligible_request_count}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                        Sufficiency threshold
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {recommendationsQuery.data.calibration_summary.thin_request_threshold}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                        Latest eligible row
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {formatTimestamp(recommendationsQuery.data.calibration_summary.latest_eligible_request_at)}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                        Rollout-disabled rows
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {recommendationsQuery.data.calibration_summary.gated_request_count}
                      </dd>
                    </div>
                  </dl>
                  <p className="mt-4 text-sm text-ink-3">
                    Keep using the ledger row and request ID correlation as the primary proof. This tenant summary only
                    explains whether replay and calibration posture are grounded by enough recent metadata-backed traffic.
                  </p>
                </article>

                <section className="panel space-y-4 px-6 py-5">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Semantic cache</div>
                    <h3 className="mt-2 text-xl font-semibold text-ink">
                      Cache effectiveness and runtime controls
                    </h3>
                    <p className="mt-2 text-sm text-ink-3">
                      This summary shows the current runtime-enforced cache posture and the supporting evidence behind it.
                      Use it to decide whether the next step is a policy preview comparison; tune these controls in the
                      existing policy editor because this page stays inspection-only.
                    </p>
                  </div>

                  <dl className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">Cache enabled</dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {recommendationsQuery.data.cache_summary.enabled ? "Yes" : "No"}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">Runtime status</dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {recommendationsQuery.data.cache_summary.runtime_status}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                        Similarity threshold
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {recommendationsQuery.data.cache_summary.similarity_threshold.toFixed(2)}
                      </dd>
                    </div>
                    <div className="rounded-2xl border border-line bg-canvas px-4 py-4">
                      <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                        Max entry age
                      </dt>
                      <dd className="mt-2 text-sm font-medium text-ink">
                        {recommendationsQuery.data.cache_summary.max_entry_age_hours} hours
                      </dd>
                    </div>
                  </dl>

                  <div className="rounded-xl border border-line bg-canvas px-4 py-3 text-sm text-ink-2">
                    <span className="font-medium text-ink">Runtime detail:</span>{" "}
                    {recommendationsQuery.data.cache_summary.runtime_detail}
                  </div>

                  {recommendationsQuery.data.cache_summary.insights.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-line px-4 py-3 text-sm text-ink-4">
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
                              <h4 className="mt-2 text-base font-semibold">
                                {insight.title}
                              </h4>
                            </div>
                            <span className="rounded-full bg-surface/70 px-3 py-1 text-xs font-semibold text-ink-2">
                              {insight.code}
                            </span>
                          </div>
                          <p className="mt-3 text-sm leading-6">{insight.summary}</p>
                          {insight.evidence.length > 0 ? (
                            <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                              {insight.evidence.map((item) => (
                                <div key={`${insight.code}-${item.label}`} className="rounded-xl bg-surface/70 px-4 py-3">
                                  <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-4">
                                    {item.label}
                                  </dt>
                                  <dd className="mt-2 text-sm font-medium text-ink">{item.value}</dd>
                                </div>
                              ))}
                            </dl>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="space-y-4">
                  <header className="panel px-6 py-5">
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">
                      Dependency health
                    </div>
                    <h3 className="mt-2 text-xl font-semibold text-ink">
                      Dependency health context
                    </h3>
                    <p className="mt-2 max-w-2xl text-sm text-ink-3">
                      These dependency states do not replace the ledger record; they provide supporting runtime context for the
                      same investigation. Required dependency failures block confidence immediately, while degraded optional
                      dependencies stay visible here so operators can explain reduced capability without losing the persisted
                      request trail.
                    </p>
                  </header>

                  {runtimeHealthQuery.isError ? (
                    <ErrorAlert error={runtimeHealthQuery.error} fallback="Unable to load dependency health." />
                  ) : (
                    <RuntimeHealthCards
                      dependencies={runtimeHealthQuery.data?.dependencies ?? {}}
                      isLoading={runtimeHealthQuery.isLoading}
                    />
                  )}
                </section>
              </>
            ) : runtimeHealthQuery.isError ? (
              <ErrorAlert error={runtimeHealthQuery.error} fallback="Unable to load dependency health." />
            ) : (
              <section className="space-y-4">
                <header className="panel px-6 py-5">
                  <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Dependency health</div>
                  <h3 className="mt-2 text-xl font-semibold text-ink">
                    Dependency health context
                  </h3>
                </header>
                <RuntimeHealthCards
                  dependencies={runtimeHealthQuery.data?.dependencies ?? {}}
                  isLoading={runtimeHealthQuery.isLoading}
                />
              </section>
            )}
          </section>
        </div>
      </section>
    </section>
  );
}
