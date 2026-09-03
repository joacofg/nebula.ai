from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

import httpx

from nebula.benchmarking.dataset import (
    PHASE5_COMPARISON_GROUP_METADATA,
    PHASE5_COMPARISON_GROUPS,
    SCENARIO_MODE_ORDER,
    BenchmarkScenario,
    ScenarioMode,
    comparison_group_for_mode,
    group_scenarios,
    load_scenarios,
)
from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import get_settings
from nebula.providers.base import CompletionUsage

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl"
DEFAULT_PRICING_PATH = PROJECT_ROOT / "benchmarks" / "pricing.json"
DEFAULT_ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts" / "benchmarks"

# Managed-local runs are a self-contained routing + cost-avoidance proof, not a
# premium-latency measurement. Pin the premium adapter to the deterministic mock
# (overriding any openai_compatible creds an operator's .env may carry) so a clean
# checkout reaches 14/14 with no network or API key. Routing, cache, fallback, and
# cost-estimate assertions are unaffected (cost is computed from pricing.json, never
# the provider bill). To benchmark a real premium provider, run a gateway with
# NEBULA_PREMIUM_PROVIDER=openai_compatible and point the runner at it via --base-url.
MANAGED_LOCAL_PREMIUM_OVERRIDES = {
    "NEBULA_PREMIUM_PROVIDER": "mock",
    "NEBULA_PREMIUM_BASE_URL": "",
    "NEBULA_PREMIUM_API_KEY": "",
}


@dataclass(slots=True)
class BenchmarkResult:
    scenario_id: str
    mode: ScenarioMode
    tags: list[str]
    status: str
    requested_model: str
    response_model: str | None
    route_target: str | None
    route_reason: str | None
    provider: str | None
    cache_hit: bool | None
    fallback_used: bool | None
    http_status: int | None
    latency_ms: float | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_premium_cost: float | None
    avoided_premium_cost: float | None
    failure_reasons: list[str]
    # The complete completion, not a trimmed one. Any trimming belongs to
    # whatever renders it, so the stored artifact stays the full evidence.
    response_content: str | None


class ManagedServer:
    def __init__(self, *, port: int, env_overrides: dict[str, str] | None = None) -> None:
        self.port = port
        self.env_overrides = env_overrides or {}
        self.process: subprocess.Popen[str] | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    async def __aenter__(self) -> "ManagedServer":
        env = os.environ.copy()
        env.update(self.env_overrides)
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "nebula.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
            ],
            cwd=PROJECT_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        await self._wait_for_health()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.process is None:
            return
        self.process.terminate()
        try:
            await asyncio.wait_for(asyncio.to_thread(self.process.wait), timeout=5)
        except TimeoutError:
            self.process.kill()
            await asyncio.to_thread(self.process.wait)

    async def _wait_for_health(self) -> None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for _ in range(40):
                try:
                    response = await client.get(f"{self.base_url}/health")
                    if response.status_code == 200:
                        return
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.5)
        raise RuntimeError(f"Nebula did not become healthy at {self.base_url}")


class BenchmarkRunner:
    def __init__(
        self,
        *,
        base_url: str | None,
        dataset_path: Path,
        pricing_path: Path,
        artifacts_root: Path,
        concurrency: int = 1,
    ) -> None:
        self.base_url = base_url
        self.dataset_path = dataset_path
        self.pricing_path = pricing_path
        self.artifacts_root = artifacts_root
        # One at a time by default. This suite reports latency, and concurrent
        # scenarios contend for the same local model, inflating the very number
        # the benchmark exists to report. Parallelism is for runs where latency
        # is not the measurement.
        if concurrency < 1:
            raise ValueError("Concurrency must be at least 1.")
        self.concurrency = concurrency
        self.settings = get_settings()
        self.scenarios = load_scenarios(dataset_path)
        self.pricing = PricingCatalog.from_path(pricing_path)
        self.run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        # Only a managed run owns its cache collections. Under --base-url the
        # runner is a client of somebody else's gateway, and deleting that
        # operator's collection would destroy a production cache.
        self.managed_collections: list[str] = (
            []
            if self.base_url
            else [
                f"nebula-benchmark-{self.run_id}-normal",
                f"nebula-benchmark-{self.run_id}-fallback",
            ]
        )
        self.collection_cleaner: Callable[[str], object] = _delete_qdrant_collection
        self.collection_cleanup: list[dict[str, str]] = []
        self.runtime_health: dict[str, object] = {"probe": "not attempted"}

    async def run(self) -> tuple[dict[str, object], Path]:
        grouped = group_scenarios(self.scenarios)
        normal_modes = [mode for mode in SCENARIO_MODE_ORDER if mode != "auto_fallback"]

        if self.base_url:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=120.0) as client:
                self.runtime_health = await self._probe_health(client)
                results = await self._run_groups(
                    client=client,
                    grouped=grouped,
                    modes=normal_modes,
                )
            results.extend(self._skipped_fallback_results(grouped["auto_fallback"]))
        else:
            # Cleanup in a finally: an interrupted run is precisely when an
            # orphan collection is left behind, so cleaning only on the happy
            # path would miss the case that motivates cleaning at all.
            try:
                results = await self._execute_managed(
                    grouped=grouped,
                    normal_modes=normal_modes,
                )
            finally:
                self.collection_cleanup = await self._cleanup_collections()

        report = self._build_report(results)
        artifact_dir = self.artifacts_root / self.run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (artifact_dir / "report.md").write_text(self._render_markdown(report), encoding="utf-8")
        return report, artifact_dir

    async def _execute_managed(
        self,
        *,
        grouped: dict[ScenarioMode, list[BenchmarkScenario]],
        normal_modes: list[ScenarioMode],
    ) -> list[BenchmarkResult]:
        results: list[BenchmarkResult] = []
        normal_collection, fallback_collection = self.managed_collections
        normal_port = _free_port()
        fallback_port = _free_port()
        async with ManagedServer(
            port=normal_port,
            env_overrides={
                **MANAGED_LOCAL_PREMIUM_OVERRIDES,
                "NEBULA_SEMANTIC_CACHE_COLLECTION": normal_collection,
            },
        ) as normal_server:
            async with httpx.AsyncClient(base_url=normal_server.base_url, timeout=120.0) as client:
                self.runtime_health = await self._probe_health(client)
                results.extend(
                    await self._run_groups(
                        client=client,
                        grouped=grouped,
                        modes=normal_modes,
                    )
                )
        async with ManagedServer(
            port=fallback_port,
            env_overrides={
                **MANAGED_LOCAL_PREMIUM_OVERRIDES,
                "NEBULA_OLLAMA_BASE_URL": "http://127.0.0.1:9",
                "NEBULA_SEMANTIC_CACHE_COLLECTION": fallback_collection,
            },
        ) as fallback_server:
            async with httpx.AsyncClient(base_url=fallback_server.base_url, timeout=120.0) as client:
                results.extend(
                    await self._run_groups(
                        client=client,
                        grouped=grouped,
                        modes=["auto_fallback"],
                    )
                )
        return results

    async def _probe_health(self, client: httpx.AsyncClient) -> dict[str, object]:
        """Ask the gateway what state its dependencies are in, before measuring.

        Twice in one week a run with Qdrant down exited 0 and produced a
        savings headline that read exactly like a healthy run's. The report has
        to know the difference, and it cannot infer it from the numbers.
        """
        try:
            response = await client.get("/health/dependencies")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"probe": "failed", "detail": str(exc)}
        payload = response.json()
        payload["probe"] = "ok"
        return payload

    def _degraded_dependencies(self) -> list[str]:
        """Dependencies that were not ready when the run started."""
        dependencies = self.runtime_health.get("dependencies")
        if not isinstance(dependencies, dict):
            return []
        return sorted(
            name
            for name, payload in dependencies.items()
            if isinstance(payload, dict)
            and str(payload.get("lifecycle_state") or payload.get("status"))
            not in {"ready", "None"}
        )

    async def _cleanup_collections(self) -> list[dict[str, str]]:
        """Drop the cache collections this run created.

        Best effort, but never silent. Qdrant may be gone by the time the run
        ends, and that must not turn a completed benchmark into a failed one —
        yet the operator still has an orphan collection to remove, so the
        outcome is recorded in the report either way.
        """
        outcomes: list[dict[str, str]] = []
        for name in self.managed_collections:
            try:
                result = self.collection_cleaner(name)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:  # noqa: BLE001 - recorded, never raised
                outcomes.append({"collection": name, "status": "failed", "detail": str(exc)})
            else:
                outcomes.append({"collection": name, "status": "deleted"})
        return outcomes

    async def _run_groups(
        self,
        *,
        client: httpx.AsyncClient,
        grouped: dict[ScenarioMode, list[BenchmarkScenario]],
        modes: list[ScenarioMode],
    ) -> list[BenchmarkResult]:
        baselines: dict[str, CompletionUsage] = {}
        results: list[BenchmarkResult] = []
        for mode in modes:
            # The barrier. Nothing in this mode starts until the previous mode
            # has fully drained, so cold finishes populating the cache before
            # warm goes looking for what it wrote.
            results.extend(
                await self._run_mode(
                    client=client,
                    scenarios=grouped[mode],
                    baselines=baselines,
                )
            )
        return results

    async def _run_mode(
        self,
        *,
        client: httpx.AsyncClient,
        scenarios: list[BenchmarkScenario],
        baselines: dict[str, CompletionUsage],
    ) -> list[BenchmarkResult]:
        """Run one mode's scenarios under a concurrency bound.

        Reads go against a snapshot frozen at the start of the mode and writes
        are staged until it ends. A scenario reading a baseline a sibling wrote
        would make the reported cost depend on completion order — which under
        any concurrency above one is not stable between runs of the same suite.
        """
        snapshot = dict(baselines)
        semaphore = asyncio.Semaphore(self.concurrency)

        async def run_one(scenario: BenchmarkScenario) -> BenchmarkResult:
            async with semaphore:
                return await self._run_scenario(
                    client=client, scenario=scenario, baselines=snapshot
                )

        # gather preserves argument order regardless of completion order, so the
        # report's raw rows stay in dataset order for a human reading them
        # against the dataset.
        results = list(await asyncio.gather(*(run_one(s) for s in scenarios)))

        for scenario, result in zip(scenarios, results, strict=True):
            if result.total_tokens:
                baselines[self._prompt_key(scenario)] = CompletionUsage(
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    total_tokens=result.total_tokens,
                )
        return results

    async def _run_scenario(
        self,
        *,
        client: httpx.AsyncClient,
        scenario: BenchmarkScenario,
        baselines: dict[str, CompletionUsage],
    ) -> BenchmarkResult:
        payload = {
            "model": self._requested_model_for_mode(scenario.mode),
            "messages": self._effective_messages(scenario),
        }
        headers = {
            "X-Nebula-API-Key": self.settings.bootstrap_api_key,
            "X-Nebula-Tenant-ID": self.settings.bootstrap_tenant_id,
        }
        started_at = time.perf_counter()
        try:
            response = await client.post("/v1/chat/completions", json=payload, headers=headers)
        except httpx.HTTPError as exc:
            return BenchmarkResult(
                scenario_id=scenario.id,
                mode=scenario.mode,
                tags=scenario.tags,
                status="failed",
                requested_model=payload["model"],
                response_model=None,
                route_target=None,
                route_reason=None,
                provider=None,
                cache_hit=None,
                fallback_used=None,
                http_status=None,
                latency_ms=None,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                estimated_premium_cost=None,
                avoided_premium_cost=None,
                failure_reasons=[str(exc)],
                response_content=None,
            )

        latency_ms = (time.perf_counter() - started_at) * 1000
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        usage = CompletionUsage(
            prompt_tokens=body.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=body.get("usage", {}).get("completion_tokens", 0),
            total_tokens=body.get("usage", {}).get("total_tokens", 0),
        )
        # The write is staged by the caller at the mode barrier, from the
        # result itself, so this stays free of shared mutable state.
        prompt_key = self._prompt_key(scenario)

        route_target = response.headers.get("X-Nebula-Route-Target")
        route_reason = response.headers.get("X-Nebula-Route-Reason")
        provider = response.headers.get("X-Nebula-Provider")
        cache_hit = response.headers.get("X-Nebula-Cache-Hit") == "true"
        fallback_used = response.headers.get("X-Nebula-Fallback-Used") == "true"
        response_model = body.get("model")
        actual_cost_model = (
            response_model
            if response_model and self.pricing.has_pricing(response_model)
            else self.settings.premium_model
        )
        estimated_premium_cost = (
            self.pricing.estimate_cost(actual_cost_model, usage)
            if route_target == "premium"
            else 0.0
        )

        avoided_premium_cost = None
        if route_target in {"local", "cache"}:
            avoided_usage = usage if route_target == "local" and usage.total_tokens else baselines.get(prompt_key)
            avoided_premium_cost = self.pricing.estimate_cost(self.settings.premium_model, avoided_usage)

        failure_reasons = self._evaluate_expectations(
            scenario=scenario,
            response=response,
            route_target=route_target,
            route_reason=route_reason,
            cache_hit=cache_hit,
            fallback_used=fallback_used,
        )

        return BenchmarkResult(
            scenario_id=scenario.id,
            mode=scenario.mode,
            tags=scenario.tags,
            status="passed" if not failure_reasons and response.status_code == 200 else "failed",
            requested_model=payload["model"],
            response_model=response_model,
            route_target=route_target,
            route_reason=route_reason,
            provider=provider,
            cache_hit=cache_hit,
            fallback_used=fallback_used,
            http_status=response.status_code,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            estimated_premium_cost=estimated_premium_cost,
            avoided_premium_cost=avoided_premium_cost,
            failure_reasons=failure_reasons,
            response_content=body.get("choices", [{}])[0].get("message", {}).get("content"),
        )

    def _build_report(self, results: list[BenchmarkResult]) -> dict[str, object]:
        executed = [result for result in results if result.status != "skipped"]
        route_distribution: dict[str, int] = {}
        http_error_counts: dict[str, int] = {}
        missing_cost_scenarios: list[str] = []
        latencies_by_mode: dict[str, list[float]] = {}
        comparison_groups: dict[str, dict[str, object]] = {
            group_id: {
                "group": group_id,
                "label": PHASE5_COMPARISON_GROUP_METADATA[group_id]["label"],
                "story_role": PHASE5_COMPARISON_GROUP_METADATA[group_id]["story_role"],
                "scenario_count": 0,
                "passed": 0,
                "failed": 0,
                "route_target_distribution": {},
                "median_latency_ms": 0.0,
                "cache_hit_rate": 0.0,
                "fallback_rate": 0.0,
                "estimated_premium_cost": 0.0,
                "estimated_premium_cost_avoided": 0.0,
                "failure_notes": [],
            }
            for group_id in PHASE5_COMPARISON_GROUPS
        }
        comparison_group_latencies: dict[str, list[float]] = {
            group_id: [] for group_id in PHASE5_COMPARISON_GROUPS
        }

        for result in executed:
            if result.route_target:
                route_distribution[result.route_target] = route_distribution.get(result.route_target, 0) + 1
            if result.http_status and result.http_status >= 400:
                key = str(result.http_status)
                http_error_counts[key] = http_error_counts.get(key, 0) + 1
            if result.latency_ms is not None:
                latencies_by_mode.setdefault(result.mode, []).append(result.latency_ms)
            if result.route_target == "premium" and result.estimated_premium_cost is None:
                missing_cost_scenarios.append(result.scenario_id)
            comparison_group_id = comparison_group_for_mode(result.mode)
            comparison_group = comparison_groups[comparison_group_id]
            comparison_group["scenario_count"] = int(comparison_group["scenario_count"]) + 1
            comparison_group[result.status] = int(comparison_group[result.status]) + 1
            if result.route_target:
                route_counts = comparison_group["route_target_distribution"]
                route_counts[result.route_target] = route_counts.get(result.route_target, 0) + 1
            if result.latency_ms is not None:
                comparison_group_latencies[comparison_group_id].append(result.latency_ms)
            if result.cache_hit:
                comparison_group["cache_hit_rate"] = float(comparison_group["cache_hit_rate"]) + 1
            if result.fallback_used:
                comparison_group["fallback_rate"] = float(comparison_group["fallback_rate"]) + 1
            comparison_group["estimated_premium_cost"] = round(
                float(comparison_group["estimated_premium_cost"]) + (result.estimated_premium_cost or 0.0),
                8,
            )
            comparison_group["estimated_premium_cost_avoided"] = round(
                float(comparison_group["estimated_premium_cost_avoided"]) + (result.avoided_premium_cost or 0.0),
                8,
            )
            if result.failure_reasons:
                comparison_group["failure_notes"].extend(result.failure_reasons)

        total_requests = len(executed)
        cache_hits = sum(1 for result in executed if result.cache_hit)
        fallbacks = sum(1 for result in executed if result.fallback_used)
        report_results = [asdict(result) for result in results]
        expectation_mismatches = {
            result.scenario_id: result.failure_reasons
            for result in executed
            if result.failure_reasons
        }
        estimated_premium_cost = round(
            sum(result.estimated_premium_cost or 0.0 for result in executed),
            8,
        )
        estimated_premium_cost_avoided = round(
            sum(result.avoided_premium_cost or 0.0 for result in executed),
            8,
        )

        for group_id, group in comparison_groups.items():
            scenario_count = int(group["scenario_count"])
            if scenario_count:
                group["cache_hit_rate"] = round(float(group["cache_hit_rate"]) / scenario_count, 4)
                group["fallback_rate"] = round(float(group["fallback_rate"]) / scenario_count, 4)
                latencies = comparison_group_latencies[group_id]
                group["median_latency_ms"] = round(median(latencies), 2) if latencies else 0.0

        cache_hit_rate = round(cache_hits / total_requests, 4) if total_requests else 0.0
        fallback_rate = round(fallbacks / total_requests, 4) if total_requests else 0.0
        key_takeaways = self._build_key_takeaways(
            total_requests=total_requests,
            estimated_premium_cost=estimated_premium_cost,
            estimated_premium_cost_avoided=estimated_premium_cost_avoided,
            route_distribution=route_distribution,
            cache_hit_rate=cache_hit_rate,
            fallback_rate=fallback_rate,
            expectation_mismatches=expectation_mismatches,
        )

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "dataset": _repo_relative(self.dataset_path),
            "cache_collections": self.collection_cleanup,
            "runtime_health": self.runtime_health,
            "degraded_dependencies": self._degraded_dependencies(),
            "base_url": self.base_url or "managed-local",
            "summary": {
                "total_requests": total_requests,
                "passed": sum(1 for result in executed if result.status == "passed"),
                "failed": sum(1 for result in executed if result.status == "failed"),
                "skipped": sum(1 for result in results if result.status == "skipped"),
                "route_distribution": route_distribution,
                "cache_hit_rate": cache_hit_rate,
                "fallback_rate": fallback_rate,
                "key_takeaways": key_takeaways,
                "comparison_groups": comparison_groups,
                "latency_by_mode_ms": {
                    mode: {
                        "p50": _percentile(latencies, 50),
                        "p95": _percentile(latencies, 95),
                        "median": round(median(latencies), 2),
                    }
                    for mode, latencies in latencies_by_mode.items()
                },
                "estimated_premium_cost": estimated_premium_cost,
                "estimated_premium_cost_avoided": estimated_premium_cost_avoided,
                "scenario_failures": expectation_mismatches,
                "expectation_mismatches": expectation_mismatches,
                "http_error_counts": http_error_counts,
                "scenarios_missing_cost_pricing": missing_cost_scenarios,
            },
            "results": report_results,
        }

    def _render_markdown(self, report: dict[str, object]) -> str:
        summary = report["summary"]
        results = report["results"]
        lines = [
            "# Nebula Benchmark Report",
            *_degraded_banner(report),
            "",
            f"- Run ID: `{report['run_id']}`",
            f"- Generated At: `{report['generated_at']}`",
            f"- Dataset: `{report['dataset']}`",
            f"- Target: `{report['base_url']}`",
            "",
            "## Summary",
            "",
            f"- Total Requests: `{summary['total_requests']}`",
            f"- Passed: `{summary['passed']}`",
            f"- Failed: `{summary['failed']}`",
            f"- Skipped: `{summary['skipped']}`",
            f"- Cache Hit Rate: `{summary['cache_hit_rate']}`",
            f"- Fallback Rate: `{summary['fallback_rate']}`",
            f"- Estimated Premium Cost: `{summary['estimated_premium_cost']}`",
            f"- Estimated Premium Cost Avoided: `{summary['estimated_premium_cost_avoided']}`",
            "",
            "## Key Takeaways",
            "",
        ]
        for takeaway in summary["key_takeaways"]:
            lines.append(f"- {takeaway}")

        lines.extend(
            [
                "",
                "## Comparison Groups",
                "",
                "| Group | Story Role | Scenarios | Passed | Median Latency (ms) | Route Mix |",
                "| --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for group in summary["comparison_groups"].values():
            lines.append(
                "| {label} | {story_role} | {scenario_count} | {passed} | {median_latency_ms} | {route_mix} |".format(
                    label=group["label"],
                    story_role=group["story_role"],
                    scenario_count=group["scenario_count"],
                    passed=group["passed"],
                    median_latency_ms=group["median_latency_ms"],
                    route_mix=self._format_route_distribution(group["route_target_distribution"]),
                )
            )

        lines.extend(
            [
                "",
                "## Route and Cost Highlights",
                "",
                f"- Route Distribution: `{self._format_route_distribution(summary['route_distribution'])}`",
                f"- Cache Hit Rate: `{summary['cache_hit_rate']}`",
                f"- Fallback Rate: `{summary['fallback_rate']}`",
                f"- Estimated Premium Cost: `{summary['estimated_premium_cost']}`",
                f"- Estimated Premium Cost Avoided: `{summary['estimated_premium_cost_avoided']}`",
                "",
                "## Scenario Results",
                "",
                "| Scenario | Mode | Status | Latency (ms) | Route | Provider | Cache | Fallback | Premium Cost | Avoided Cost |",
                "| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |",
            ]
        )
        for result in results:
            lines.append(
                "| {scenario_id} | {mode} | {status} | {latency_ms} | {route_target} | {provider} | {cache_hit} | {fallback_used} | {estimated_premium_cost} | {avoided_premium_cost} |".format(
                    scenario_id=result["scenario_id"],
                    mode=result["mode"],
                    status=result["status"],
                    latency_ms=result["latency_ms"] if result["latency_ms"] is not None else "-",
                    route_target=result["route_target"] or "-",
                    provider=result["provider"] or "-",
                    cache_hit=result["cache_hit"],
                    fallback_used=result["fallback_used"],
                    estimated_premium_cost=result["estimated_premium_cost"]
                    if result["estimated_premium_cost"] is not None
                    else "-",
                    avoided_premium_cost=result["avoided_premium_cost"]
                    if result["avoided_premium_cost"] is not None
                    else "-",
                )
            )

        if summary["expectation_mismatches"]:
            lines.extend(["", "## Expectation Mismatches", ""])
            for scenario_id, reasons in summary["expectation_mismatches"].items():
                lines.append(f"- `{scenario_id}`: {', '.join(reasons)}")

        return "\n".join(lines) + "\n"

    def _build_key_takeaways(
        self,
        *,
        total_requests: int,
        estimated_premium_cost: float,
        estimated_premium_cost_avoided: float,
        route_distribution: dict[str, int],
        cache_hit_rate: float,
        fallback_rate: float,
        expectation_mismatches: dict[str, list[str]],
    ) -> list[str]:
        takeaways = [
            (
                "Nebula avoided an estimated premium spend of "
                f"{estimated_premium_cost_avoided} across {total_requests} executed requests while "
                f"keeping measured premium spend at {estimated_premium_cost}."
            ),
            (
                "Route mix favored "
                f"{self._format_route_distribution(route_distribution)}, showing how local, cache, and premium paths split in one repeatable run."
            ),
            (
                "Warm-cache and fallback behavior stayed explicit with "
                f"cache_hit_rate={cache_hit_rate} and fallback_rate={fallback_rate}."
            ),
        ]
        if expectation_mismatches:
            takeaways.append(
                "Expectation mismatches were detected in "
                f"{', '.join(sorted(expectation_mismatches))}."
            )
        else:
            takeaways.append("All executed scenarios matched their expected route, cache, and fallback outcomes.")
        return takeaways

    def _format_route_distribution(self, route_distribution: dict[str, int]) -> str:
        if not route_distribution:
            return "-"
        return ", ".join(
            f"{route}:{count}" for route, count in sorted(route_distribution.items(), key=lambda item: item[0])
        )

    def _effective_messages(self, scenario: BenchmarkScenario) -> list[dict[str, object]]:
        messages: list[dict[str, object]] = []
        for message in scenario.messages:
            updated_message = dict(message)
            if updated_message.get("role") == "user" and isinstance(updated_message.get("content"), str):
                updated_message["content"] = (
                    f"[benchmark:{self.run_id}:{scenario.id}] {updated_message['content']}"
                )
            messages.append(updated_message)
        return messages

    def _evaluate_expectations(
        self,
        *,
        scenario: BenchmarkScenario,
        response: httpx.Response,
        route_target: str | None,
        route_reason: str | None,
        cache_hit: bool,
        fallback_used: bool,
    ) -> list[str]:
        reasons: list[str] = []
        if response.status_code != 200:
            reasons.append(f"Expected status 200, received {response.status_code}")
        if route_target != scenario.expect.route_target:
            reasons.append(f"Expected route target {scenario.expect.route_target}, received {route_target}")
        if route_reason != scenario.expect.route_reason:
            reasons.append(f"Expected route reason {scenario.expect.route_reason}, received {route_reason}")
        if cache_hit != scenario.expect.cache_hit:
            reasons.append(f"Expected cache_hit={scenario.expect.cache_hit}, received {cache_hit}")
        if fallback_used != scenario.expect.fallback_used:
            reasons.append(
                f"Expected fallback_used={scenario.expect.fallback_used}, received {fallback_used}"
            )
        return reasons

    def _requested_model_for_mode(self, mode: ScenarioMode) -> str:
        if mode == "premium_direct":
            return self.settings.premium_model
        if mode == "local_direct":
            return self.settings.local_model
        return self.settings.default_model

    def _prompt_key(self, scenario: BenchmarkScenario) -> str:
        user_messages = [
            message["content"]
            for message in scenario.messages
            if message.get("role") == "user" and isinstance(message.get("content"), str)
        ]
        return "|".join(user_messages)

    def _skipped_fallback_results(self, scenarios: list[BenchmarkScenario]) -> list[BenchmarkResult]:
        results: list[BenchmarkResult] = []
        for scenario in scenarios:
            results.append(
                BenchmarkResult(
                    scenario_id=scenario.id,
                    mode=scenario.mode,
                    tags=scenario.tags,
                    status="skipped",
                    requested_model=self._requested_model_for_mode(scenario.mode),
                    response_model=None,
                    route_target=None,
                    route_reason=None,
                    provider=None,
                    cache_hit=None,
                    fallback_used=None,
                    http_status=None,
                    latency_ms=None,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    estimated_premium_cost=None,
                    avoided_premium_cost=None,
                    failure_reasons=["Fallback scenarios require a managed local Nebula server."],
                    response_content=None,
                )
            )
        return results


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return round(ordered[lower], 2)
    fraction = position - lower
    interpolated = ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
    return round(interpolated, 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Nebula benchmark scenarios.")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL"))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--pricing", default=str(DEFAULT_PRICING_PATH))
    parser.add_argument("--artifacts-root", default=str(DEFAULT_ARTIFACTS_ROOT))
    return parser.parse_args()


async def _async_main() -> None:
    args = parse_args()
    runner = BenchmarkRunner(
        base_url=args.base_url,
        dataset_path=Path(args.dataset),
        pricing_path=Path(args.pricing),
        artifacts_root=Path(args.artifacts_root),
    )
    report, artifact_dir = await runner.run()
    print(f"Benchmark complete: {artifact_dir}")
    print(json.dumps(report["summary"], indent=2))


def main() -> None:
    asyncio.run(_async_main())


def _degraded_banner(report: dict[str, object]) -> list[str]:
    """A banner a reader cannot miss when the run was not measuring a healthy stack.

    A savings figure from a run with the semantic cache unreachable looks
    identical to one from a healthy run. Nothing else on the page distinguishes
    them, so the distinction has to be stated.
    """
    health = report.get("runtime_health")
    probe = health.get("probe") if isinstance(health, dict) else None
    degraded = report.get("degraded_dependencies") or []

    if probe == "failed":
        return [
            "> **NOT COMPARABLE.** The dependency-health probe failed, so this run "
            "was measured against a stack of unknown state. Do not compare these "
            "numbers with a healthy run.",
            "",
        ]
    if degraded:
        names = ", ".join(f"`{name}`" for name in degraded)
        return [
            f"> **NOT COMPARABLE.** These dependencies were not ready when the run "
            f"started: {names}. Cache-dependent figures below reflect a degraded "
            f"stack and cannot be compared with a healthy run.",
            "",
        ]
    return []


def _repo_relative(path: Path) -> str:
    """Record a path relative to the repo when it is inside it, absolute when not.

    relative_to() raises for anything outside PROJECT_ROOT, and this is called
    from _build_report — after every scenario has run — so a --dataset pointing
    anywhere else used to throw away the whole run at the very last step.
    """
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


async def _delete_qdrant_collection(name: str) -> None:
    """Drop a benchmark's cache collection.

    Async, matching semantic_cache_service, so cleanup does not block the event
    loop. Imported lazily so the runner still loads, and still reports, on a
    machine where the Qdrant client cannot be constructed.
    """
    from qdrant_client import AsyncQdrantClient

    settings = get_settings()
    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        await client.delete_collection(collection_name=name)
    finally:
        await client.close()

if __name__ == "__main__":
    main()
