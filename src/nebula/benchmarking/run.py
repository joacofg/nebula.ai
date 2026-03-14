from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

import httpx

from nebula.benchmarking.dataset import (
    SCENARIO_MODE_ORDER,
    BenchmarkScenario,
    ScenarioMode,
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
    response_preview: str | None


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
    ) -> None:
        self.base_url = base_url
        self.dataset_path = dataset_path
        self.pricing_path = pricing_path
        self.artifacts_root = artifacts_root
        self.settings = get_settings()
        self.scenarios = load_scenarios(dataset_path)
        self.pricing = PricingCatalog.from_path(pricing_path)
        self.run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    async def run(self) -> tuple[dict[str, object], Path]:
        grouped = group_scenarios(self.scenarios)
        normal_modes = [mode for mode in SCENARIO_MODE_ORDER if mode != "auto_fallback"]
        results: list[BenchmarkResult] = []

        if self.base_url:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=120.0) as client:
                results.extend(
                    await self._run_groups(
                        client=client,
                        grouped=grouped,
                        modes=normal_modes,
                    )
                )
            results.extend(self._skipped_fallback_results(grouped["auto_fallback"]))
        else:
            normal_port = _free_port()
            fallback_port = _free_port()
            async with ManagedServer(
                port=normal_port,
                env_overrides={
                    "NEBULA_SEMANTIC_CACHE_COLLECTION": f"nebula-benchmark-{self.run_id}-normal",
                },
            ) as normal_server:
                async with httpx.AsyncClient(base_url=normal_server.base_url, timeout=120.0) as client:
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
                    "NEBULA_OLLAMA_BASE_URL": "http://127.0.0.1:9",
                    "NEBULA_SEMANTIC_CACHE_COLLECTION": f"nebula-benchmark-{self.run_id}-fallback",
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

        report = self._build_report(results)
        artifact_dir = self.artifacts_root / self.run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (artifact_dir / "report.md").write_text(self._render_markdown(report), encoding="utf-8")
        return report, artifact_dir

    async def _run_groups(
        self,
        *,
        client: httpx.AsyncClient,
        grouped: dict[ScenarioMode, list[BenchmarkScenario]],
        modes: list[ScenarioMode],
    ) -> list[BenchmarkResult]:
        prompt_baselines: dict[str, CompletionUsage] = {}
        results: list[BenchmarkResult] = []
        for mode in modes:
            for scenario in grouped[mode]:
                result = await self._run_scenario(client=client, scenario=scenario, prompt_baselines=prompt_baselines)
                results.append(result)
        return results

    async def _run_scenario(
        self,
        *,
        client: httpx.AsyncClient,
        scenario: BenchmarkScenario,
        prompt_baselines: dict[str, CompletionUsage],
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
                response_preview=None,
            )

        latency_ms = (time.perf_counter() - started_at) * 1000
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        usage = CompletionUsage(
            prompt_tokens=body.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=body.get("usage", {}).get("completion_tokens", 0),
            total_tokens=body.get("usage", {}).get("total_tokens", 0),
        )
        prompt_key = self._prompt_key(scenario)
        if usage.total_tokens:
            prompt_baselines[prompt_key] = usage

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
            avoided_usage = usage if route_target == "local" and usage.total_tokens else prompt_baselines.get(prompt_key)
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
            response_preview=body.get("choices", [{}])[0].get("message", {}).get("content"),
        )

    def _build_report(self, results: list[BenchmarkResult]) -> dict[str, object]:
        executed = [result for result in results if result.status != "skipped"]
        route_distribution: dict[str, int] = {}
        http_error_counts: dict[str, int] = {}
        missing_cost_scenarios: list[str] = []
        latencies_by_mode: dict[str, list[float]] = {}

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

        total_requests = len(executed)
        cache_hits = sum(1 for result in executed if result.cache_hit)
        fallbacks = sum(1 for result in executed if result.fallback_used)
        report_results = [asdict(result) for result in results]

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "dataset": str(self.dataset_path.relative_to(PROJECT_ROOT)),
            "base_url": self.base_url or "managed-local",
            "summary": {
                "total_requests": total_requests,
                "passed": sum(1 for result in executed if result.status == "passed"),
                "failed": sum(1 for result in executed if result.status == "failed"),
                "skipped": sum(1 for result in results if result.status == "skipped"),
                "route_distribution": route_distribution,
                "cache_hit_rate": round(cache_hits / total_requests, 4) if total_requests else 0.0,
                "fallback_rate": round(fallbacks / total_requests, 4) if total_requests else 0.0,
                "latency_by_mode_ms": {
                    mode: {
                        "p50": _percentile(latencies, 50),
                        "p95": _percentile(latencies, 95),
                        "median": round(median(latencies), 2),
                    }
                    for mode, latencies in latencies_by_mode.items()
                },
                "estimated_premium_cost": round(
                    sum(result.estimated_premium_cost or 0.0 for result in executed),
                    8,
                ),
                "estimated_premium_cost_avoided": round(
                    sum(result.avoided_premium_cost or 0.0 for result in executed),
                    8,
                ),
                "scenario_failures": {
                    result.scenario_id: result.failure_reasons
                    for result in executed
                    if result.failure_reasons
                },
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
            "## Scenario Results",
            "",
            "| Scenario | Mode | Status | Latency (ms) | Route | Provider | Cache | Fallback | Premium Cost | Avoided Cost |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |",
        ]
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

        if summary["scenario_failures"]:
            lines.extend(["", "## Failures", ""])
            for scenario_id, reasons in summary["scenario_failures"].items():
                lines.append(f"- `{scenario_id}`: {', '.join(reasons)}")

        return "\n".join(lines) + "\n"

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
                    response_preview=None,
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


if __name__ == "__main__":
    main()
