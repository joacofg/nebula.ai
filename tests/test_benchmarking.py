from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
import pytest

from nebula.benchmarking.dataset import (
    PHASE5_COMPARISON_GROUPS,
    BenchmarkScenario,
    SCENARIO_MODE_ORDER,
    comparison_group_for_mode,
    group_scenarios,
    load_scenarios,
)
from nebula.benchmarking.pricing import PricingCatalog
from nebula.benchmarking.run import BenchmarkResult, BenchmarkRunner
from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionUsage
from nebula.services.router_service import RouterService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
@pytest.mark.parametrize("dataset", ["scenarios.jsonl", "demo-scenarios.jsonl"])
async def test_auto_heuristic_scenarios_expect_reasons_the_router_emits(dataset) -> None:
    """Guard against route-reason vocabulary drift.

    The heuristic auto routes (cold simple, complex) get their route_reason
    straight from RouterService. M006 unified those reasons to "token_complexity";
    a dataset expecting a retired reason (e.g. "simple_prompt",
    "complexity_hint") would silently fail every benchmark run. This pins the
    eval expectations to what the router actually produces — no live services.

    Both datasets, because the guard used to read only the full suite. The demo
    subset drifted to a retired reason and stayed there: make benchmark-demo,
    the one run in front of an audience, reported a failed expectation on every
    single run and no test noticed.
    """
    scenarios = load_scenarios(PROJECT_ROOT / "benchmarks" / "v1" / dataset)
    router = RouterService(Settings())

    heuristic = [s for s in scenarios if s.mode in {"auto_simple_cold", "auto_complex"}]
    assert heuristic, "expected auto heuristic scenarios in the dataset"

    for scenario in heuristic:
        prompt = "\n".join(
            str(m["content"])
            for m in scenario.messages
            if m.get("role") == "user" and isinstance(m.get("content"), str)
        )
        decision = await router.choose_target_with_reason(
            prompt,
            ChatCompletionRequest(model="nebula-auto", messages=scenario.messages),
        )
        assert decision.reason == scenario.expect.route_reason, (
            f"{scenario.id}: router emits {decision.reason!r}, "
            f"scenario expects {scenario.expect.route_reason!r}"
        )
        assert decision.target == scenario.expect.route_target, (
            f"{scenario.id}: router targets {decision.target!r}, "
            f"scenario expects {scenario.expect.route_target!r}"
        )


def test_load_scenarios_and_group_by_expected_order() -> None:
    scenarios = load_scenarios(PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl")
    grouped = group_scenarios(scenarios)

    assert len(scenarios) == 14
    assert list(grouped) == list(SCENARIO_MODE_ORDER)
    assert len(grouped["auto_simple_cold"]) == 3
    assert len(grouped["auto_simple_warm"]) == 3
    assert grouped["auto_fallback"][0].expect.fallback_used is True


def test_phase5_comparison_group_mapping_matches_product_story() -> None:
    assert list(PHASE5_COMPARISON_GROUPS) == [
        "premium_control",
        "local_control",
        "auto_routing_cold",
        "auto_routing_warm_cache",
        "fallback_resilience",
        "premium_supporting_evidence",
    ]
    assert comparison_group_for_mode("premium_direct") == "premium_control"
    assert comparison_group_for_mode("local_direct") == "local_control"
    assert comparison_group_for_mode("auto_simple_cold") == "auto_routing_cold"
    assert comparison_group_for_mode("auto_simple_warm") == "auto_routing_warm_cache"
    assert comparison_group_for_mode("auto_fallback") == "fallback_resilience"
    assert comparison_group_for_mode("auto_complex") == "premium_supporting_evidence"


def test_phase5_demo_subset_preserves_story_beats_and_order() -> None:
    demo_scenarios = load_scenarios(PROJECT_ROOT / "benchmarks" / "v1" / "demo-scenarios.jsonl")

    assert [scenario.mode for scenario in demo_scenarios] == [
        "premium_direct",
        "local_direct",
        "auto_simple_cold",
        "auto_simple_warm",
        "auto_fallback",
    ]
    assert [scenario.id for scenario in demo_scenarios] == [
        "premium-direct-brief",
        "local-direct-brief",
        "auto-simple-cold-1",
        "auto-simple-warm-1",
        "auto-fallback-hello",
    ]


def test_pricing_catalog_estimates_paid_and_free_models() -> None:
    pricing = PricingCatalog.from_path(PROJECT_ROOT / "benchmarks" / "pricing.json")
    usage = CompletionUsage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)

    paid_cost = pricing.estimate_cost("openai/gpt-4o-mini", usage)
    paid_alias_cost = pricing.estimate_cost("gpt-4o-mini", usage)

    assert paid_cost == 0.00045
    assert paid_alias_cost == 0.00045
    assert paid_cost > 0


def test_benchmark_runner_builds_report_and_markdown_shapes(tmp_path) -> None:
    runner = BenchmarkRunner(
        base_url="http://127.0.0.1:8000",
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )
    results = [
        BenchmarkResult(
            scenario_id="premium-direct-brief",
            mode="premium_direct",
            tags=["control", "premium"],
            status="passed",
            requested_model="gpt-4o-mini",
            response_model="openai/gpt-4o-mini",
            route_target="premium",
            route_reason="explicit_premium_model",
            provider="openai-compatible",
            cache_hit=False,
            fallback_used=False,
            http_status=200,
            latency_ms=800.0,
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
            estimated_premium_cost=0.0004,
            avoided_premium_cost=None,
            failure_reasons=[],
            response_content="premium",
        ),
        BenchmarkResult(
            scenario_id="local-direct-brief",
            mode="local_direct",
            tags=["local"],
            status="passed",
            requested_model="llama3.2:3b",
            response_model="llama3.2:3b",
            route_target="local",
            route_reason="explicit_local_model",
            provider="ollama",
            cache_hit=False,
            fallback_used=False,
            http_status=200,
            latency_ms=42.0,
            prompt_tokens=12,
            completion_tokens=8,
            total_tokens=20,
            estimated_premium_cost=0.0,
            avoided_premium_cost=0.0000066,
            failure_reasons=[],
            response_content="local",
        ),
        BenchmarkResult(
            scenario_id="auto-simple-cold-1",
            mode="auto_simple_cold",
            tags=["auto", "cache", "simple"],
            status="passed",
            requested_model="nebula-auto",
            response_model="llama3.2:3b",
            route_target="local",
            route_reason="simple_prompt",
            provider="ollama",
            cache_hit=False,
            fallback_used=False,
            http_status=200,
            latency_ms=60.0,
            prompt_tokens=10,
            completion_tokens=6,
            total_tokens=16,
            estimated_premium_cost=0.0,
            avoided_premium_cost=0.000005,
            failure_reasons=[],
            response_content="cold",
        ),
        BenchmarkResult(
            scenario_id="auto-simple-warm-1",
            mode="auto_simple_warm",
            tags=["auto", "cache", "warm"],
            status="passed",
            requested_model="nebula-auto",
            response_model="cache",
            route_target="cache",
            route_reason="cache_hit",
            provider="cache",
            cache_hit=True,
            fallback_used=False,
            http_status=200,
            latency_ms=8.0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_premium_cost=0.0,
            avoided_premium_cost=0.000005,
            failure_reasons=[],
            response_content="warm",
        ),
        BenchmarkResult(
            scenario_id="auto-complex-architecture",
            mode="auto_complex",
            tags=["auto", "premium", "complex"],
            status="passed",
            requested_model="nebula-auto",
            response_model="openai/gpt-4o-mini",
            route_target="premium",
            route_reason="token_complexity",
            provider="openai-compatible",
            cache_hit=False,
            fallback_used=False,
            http_status=200,
            latency_ms=1500.0,
            prompt_tokens=220,
            completion_tokens=90,
            total_tokens=310,
            estimated_premium_cost=0.0012,
            avoided_premium_cost=None,
            failure_reasons=[],
            response_content="complex",
        ),
        BenchmarkResult(
            scenario_id="auto-fallback-hello",
            mode="auto_fallback",
            tags=["fallback"],
            status="failed",
            requested_model="nebula-auto",
            response_model="openai/gpt-4o-mini",
            route_target="premium",
            route_reason="local_provider_error_fallback",
            provider="openai-compatible",
            cache_hit=False,
            fallback_used=True,
            http_status=502,
            latency_ms=120.0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_premium_cost=0.0,
            avoided_premium_cost=None,
            failure_reasons=["Expected status 200, received 502"],
            response_content=None,
        ),
    ]

    report = runner._build_report(results)
    markdown = runner._render_markdown(report)

    assert report["summary"]["total_requests"] == 6
    assert report["summary"]["route_distribution"]["local"] == 2
    assert report["summary"]["route_distribution"]["premium"] == 3
    assert report["summary"]["route_distribution"]["cache"] == 1
    assert report["summary"]["fallback_rate"] == pytest.approx(1 / 6, rel=0, abs=1e-4)
    assert report["summary"]["estimated_premium_cost"] == 0.0016
    assert report["summary"]["estimated_premium_cost_avoided"] == 0.0000166
    assert report["summary"]["key_takeaways"][0].startswith("Nebula avoided an estimated premium spend")
    assert report["summary"]["expectation_mismatches"]["auto-fallback-hello"] == [
        "Expected status 200, received 502",
    ]
    assert report["summary"]["comparison_groups"]["premium_control"]["scenario_count"] == 1
    assert report["summary"]["comparison_groups"]["local_control"]["route_target_distribution"]["local"] == 1
    assert report["summary"]["comparison_groups"]["auto_routing_warm_cache"]["cache_hit_rate"] == 1.0
    assert report["summary"]["comparison_groups"]["fallback_resilience"]["failure_notes"] == [
        "Expected status 200, received 502",
    ]
    assert report["summary"]["comparison_groups"]["premium_supporting_evidence"]["story_role"].startswith(
        "Supporting evidence"
    )
    assert report["summary"]["comparison_groups"]["auto_routing_cold"]["median_latency_ms"] == 60.0
    assert report["results"][0]["scenario_id"] == "premium-direct-brief"

    assert "# Nebula Benchmark Report" in markdown
    assert "## Key Takeaways" in markdown
    assert "## Comparison Groups" in markdown
    assert "## Route and Cost Highlights" in markdown
    assert "## Expectation Mismatches" in markdown
    assert "| Group | Story Role | Scenarios | Passed | Median Latency (ms) | Route Mix |" in markdown
    assert "| local-direct-brief |" in markdown
    assert "premium_supporting_evidence" not in markdown
    assert "Supporting premium-routed evidence" in markdown


def test_makefile_exposes_demo_benchmark_target() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "benchmark-demo:" in makefile
    assert "--dataset benchmarks/v1/demo-scenarios.jsonl" in makefile


@pytest.mark.asyncio
async def test_benchmark_runner_authenticates_requests_as_a_tenant(tmp_path) -> None:
    runner = BenchmarkRunner(
        base_url="http://127.0.0.1:8000",
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )
    scenario = load_scenarios(PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl")[0]
    captured_headers = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_headers["X-Nebula-API-Key"] = request.headers.get("X-Nebula-API-Key")
        captured_headers["X-Nebula-Tenant-ID"] = request.headers.get("X-Nebula-Tenant-ID")
        return httpx.Response(
            200,
            headers={
                "X-Nebula-Route-Target": "local",
                "X-Nebula-Route-Reason": "explicit_local_model",
                "X-Nebula-Provider": "ollama",
                "X-Nebula-Cache-Hit": "false",
                "X-Nebula-Fallback-Used": "false",
            },
            json={
                "model": "llama3.2:3b",
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
            },
        )

    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000",
        transport=httpx.MockTransport(handler),
    ) as client:
        await runner._run_scenario(client=client, scenario=scenario, baselines={})

    assert captured_headers["X-Nebula-API-Key"] == runner.settings.bootstrap_api_key
    assert captured_headers["X-Nebula-Tenant-ID"] == runner.settings.bootstrap_tenant_id


# --- T11: response_preview -> response_content --------------------------------


GOLDEN_REPORT = PROJECT_ROOT / "tests" / "golden" / "benchmark_report.md"


def _mask_volatile(markdown: str) -> str:
    """Blank the two lines that change on every render."""
    import re

    markdown = re.sub(r"^- Run ID: `.*`$", "- Run ID: `<run-id>`", markdown, flags=re.M)
    return re.sub(
        r"^- Generated At: `.*`$", "- Generated At: `<generated-at>`", markdown, flags=re.M
    )


def _regression_result(
    scenario_id: str,
    mode: str,
    route_target: str,
    route_reason: str,
    provider: str,
    latency_ms: float,
    prompt_tokens: int,
    completion_tokens: int,
    estimated_premium_cost: float,
    avoided_premium_cost: float | None,
    content: str,
) -> BenchmarkResult:
    return BenchmarkResult(
        scenario_id=scenario_id,
        mode=mode,
        tags=["t"],
        status="passed",
        requested_model="m",
        response_model="m",
        route_target=route_target,
        route_reason=route_reason,
        provider=provider,
        cache_hit=False,
        fallback_used=False,
        http_status=200,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_premium_cost=estimated_premium_cost,
        avoided_premium_cost=avoided_premium_cost,
        failure_reasons=[],
        response_content=content,
    )


def _regression_runner(tmp_path) -> BenchmarkRunner:
    return BenchmarkRunner(
        base_url="http://127.0.0.1:8000",
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )


def _regression_results() -> list[BenchmarkResult]:
    return [
        _regression_result(
            "p1", "premium_direct", "premium", "explicit_premium_model",
            "openai-compatible", 800.0, 100, 20, 0.0004, None, "premium body",
        ),
        _regression_result(
            "l1", "local_direct", "local", "explicit_local_model",
            "ollama", 42.0, 12, 8, 0.0, 0.0000066, "local body",
        ),
        _regression_result(
            "c1", "auto_simple_cold", "local", "simple_prompt",
            "ollama", 60.0, 10, 6, 0.0, 0.000005, "cold body",
        ),
    ]


def test_the_result_field_is_named_for_what_it_holds(tmp_path) -> None:
    # The field has always stored the complete completion, never a preview of
    # it. A name that says otherwise invites a caller to render it raw.
    result = _regression_results()[0]

    assert result.response_content == "premium body"
    assert not hasattr(result, "response_preview")


def test_the_report_rows_carry_response_content(tmp_path) -> None:
    runner = _regression_runner(tmp_path)

    report = runner._build_report(_regression_results())

    assert "response_content" in report["results"][0]
    assert "response_preview" not in report["results"][0]


def test_renaming_the_field_leaves_the_rendered_report_byte_identical(tmp_path) -> None:
    # The golden was captured before the rename. report.md is what a reader
    # actually reads, and the rename must not have moved a character of it.
    runner = _regression_runner(tmp_path)

    rendered = runner._render_markdown(runner._build_report(_regression_results()))

    assert _mask_volatile(rendered) == GOLDEN_REPORT.read_text(encoding="utf-8")


# --- T5: ephemeral Qdrant collections ------------------------------------------


def test_ephemeral_collection_names_are_scoped_to_the_run(tmp_path) -> None:
    runner = BenchmarkRunner(
        base_url=None,
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )

    assert runner.managed_collections == [
        f"nebula-benchmark-{runner.run_id}-normal",
        f"nebula-benchmark-{runner.run_id}-fallback",
    ]


def test_an_external_run_owns_no_ephemeral_collection(tmp_path) -> None:
    # With --base-url the runner is a client of somebody else's gateway. The
    # collection belongs to that operator, and deleting it would destroy a
    # production cache.
    runner = BenchmarkRunner(
        base_url="http://127.0.0.1:8000",
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )

    assert runner.managed_collections == []


@pytest.mark.asyncio
async def test_ephemeral_collection_cleanup_deletes_every_collection_it_owns(tmp_path) -> None:
    runner = BenchmarkRunner(
        base_url=None,
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )
    deleted: list[str] = []
    runner.collection_cleaner = deleted.append

    outcomes = await runner._cleanup_collections()

    assert deleted == runner.managed_collections
    assert [outcome["status"] for outcome in outcomes] == ["deleted", "deleted"]


@pytest.mark.asyncio
async def test_ephemeral_collection_cleanup_records_a_failure_without_failing_the_run(
    tmp_path,
) -> None:
    # Qdrant may be down by the time the run ends. That must not turn a
    # completed benchmark into a failed one, and it must not pass silently
    # either: the operator has an orphan collection to go and remove.
    runner = BenchmarkRunner(
        base_url=None,
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )

    def refuse(name: str) -> None:
        raise ConnectionError("qdrant unreachable")

    runner.collection_cleaner = refuse
    outcomes = await runner._cleanup_collections()

    assert [outcome["status"] for outcome in outcomes] == ["failed", "failed"]
    assert all("qdrant unreachable" in outcome["detail"] for outcome in outcomes)


@pytest.mark.asyncio
async def test_ephemeral_collection_is_cleaned_up_even_when_the_run_raises(tmp_path) -> None:
    # An interrupted run is exactly when an orphan collection is created, so
    # cleanup on the happy path only would miss the case that motivates it.
    cleaned: list[str] = []

    class ExplodingRunner(BenchmarkRunner):
        async def _execute_managed(self, **_: object) -> list[BenchmarkResult]:
            raise KeyboardInterrupt("operator stopped the run")

    runner = ExplodingRunner(
        base_url=None,
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )
    runner.collection_cleaner = cleaned.append

    with pytest.raises(KeyboardInterrupt):
        await runner.run()

    assert cleaned == runner.managed_collections


@pytest.mark.asyncio
async def test_the_report_records_which_collections_the_run_owned(tmp_path) -> None:
    runner = BenchmarkRunner(
        base_url=None,
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )
    runner.collection_cleaner = lambda name: None
    runner.collection_cleanup = await runner._cleanup_collections()

    report = runner._build_report(_regression_results())

    assert [entry["collection"] for entry in report["cache_collections"]] == (
        runner.managed_collections
    )


@pytest.mark.asyncio
async def test_ephemeral_collection_cleanup_awaits_an_async_cleaner(tmp_path) -> None:
    # The real cleaner is async, so this is the branch production takes. A
    # sync-only test would leave it unexercised and the coroutine would be
    # created and dropped without ever deleting anything.
    runner = BenchmarkRunner(
        base_url=None,
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )
    deleted: list[str] = []

    async def delete(name: str) -> None:
        deleted.append(name)

    runner.collection_cleaner = delete
    outcomes = await runner._cleanup_collections()

    assert deleted == runner.managed_collections
    assert [outcome["status"] for outcome in outcomes] == ["deleted", "deleted"]


@pytest.mark.asyncio
async def test_ephemeral_collection_cleanup_records_an_async_failure(tmp_path) -> None:
    runner = BenchmarkRunner(
        base_url=None,
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )

    async def refuse(name: str) -> None:
        raise ConnectionError("qdrant unreachable")

    runner.collection_cleaner = refuse
    outcomes = await runner._cleanup_collections()

    assert [outcome["status"] for outcome in outcomes] == ["failed", "failed"]


def test_the_runner_is_importable_and_runnable_as_a_module(tmp_path) -> None:
    # Importing the module defines every top-level name; running it as __main__
    # calls main() at the point the guard sits, so anything defined below that
    # guard does not exist yet. Only executing the module catches that, which
    # is why the unit tests above cannot.
    import subprocess
    import sys

    dataset = tmp_path / "empty.jsonl"
    dataset.write_text("", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "nebula.benchmarking.run",
            "--base-url",
            "http://127.0.0.1:1",
            "--dataset",
            str(dataset),
            "--artifacts-root",
            str(tmp_path / "artifacts"),
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    assert "NameError" not in completed.stderr
    assert completed.returncode == 0, completed.stderr[-2000:]


def test_a_dataset_outside_the_repo_does_not_lose_the_run_at_report_time(tmp_path) -> None:
    # The report recorded the dataset as a repo-relative path, which throws for
    # any dataset elsewhere. The throw lands in _build_report, after every
    # scenario has already been executed, so the whole run is lost at the last
    # step.
    dataset = tmp_path / "elsewhere.jsonl"
    dataset.write_text("", encoding="utf-8")
    runner = BenchmarkRunner(
        base_url="http://127.0.0.1:8000",
        dataset_path=dataset,
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
    )

    report = runner._build_report(_regression_results())

    assert report["dataset"] == str(dataset)


def test_a_dataset_inside_the_repo_is_still_recorded_relative(tmp_path) -> None:
    runner = _regression_runner(tmp_path)

    report = runner._build_report(_regression_results())

    assert report["dataset"] == "benchmarks/v1/scenarios.jsonl"


# --- T9: bounded concurrency per mode, with a barrier between modes ------------


class _TracingRunner(BenchmarkRunner):
    """Records when each scenario starts and ends, without touching a server."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.trace: list[tuple[str, str]] = []
        self.seen_baselines: dict[str, dict[str, int]] = {}

    async def _run_scenario(self, *, client, scenario, baselines):
        self.trace.append((scenario.id, "start"))
        self.seen_baselines[scenario.id] = {
            key: usage.total_tokens for key, usage in baselines.items()
        }
        for _ in range(3):
            await asyncio.sleep(0)
        self.trace.append((scenario.id, "end"))
        return _regression_result(
            scenario.id, scenario.mode, "premium", "explicit_premium_model",
            "openai-compatible", 10.0, 5, 5, 0.0, None, "body",
        )


def _tracing_runner(tmp_path, **kwargs) -> _TracingRunner:
    return _TracingRunner(
        base_url="http://127.0.0.1:8000",
        dataset_path=PROJECT_ROOT / "benchmarks" / "v1" / "scenarios.jsonl",
        pricing_path=PROJECT_ROOT / "benchmarks" / "pricing.json",
        artifacts_root=tmp_path,
        **kwargs,
    )


def _fake_grouped(counts: dict[str, int]) -> dict[str, list[BenchmarkScenario]]:
    from nebula.benchmarking.dataset import ScenarioExpectation

    return {
        mode: [
            BenchmarkScenario(
                id=f"{mode}-{index}",
                mode=mode,
                messages=[{"role": "user", "content": f"{mode} {index}"}],
                tags=[],
                expect=ScenarioExpectation(
                    route_target="premium",
                    route_reason="explicit_premium_model",
                    cache_hit=False,
                    fallback_used=False,
                ),
            )
            for index in range(count)
        ]
        for mode, count in counts.items()
    }


@pytest.mark.asyncio
async def test_mode_barrier_drains_a_mode_before_the_next_one_starts(tmp_path) -> None:
    # Cold has to populate the cache before warm reads it. Without a barrier a
    # warm scenario can start while cold is still in flight and miss the entry
    # it was written to find.
    runner = _tracing_runner(tmp_path, concurrency=4)
    grouped = _fake_grouped({"auto_simple_cold": 3, "auto_simple_warm": 3})

    await runner._run_groups(
        client=None, grouped=grouped, modes=["auto_simple_cold", "auto_simple_warm"]
    )

    last_cold_end = max(
        index for index, (sid, event) in enumerate(runner.trace)
        if sid.startswith("auto_simple_cold") and event == "end"
    )
    first_warm_start = min(
        index for index, (sid, event) in enumerate(runner.trace)
        if sid.startswith("auto_simple_warm") and event == "start"
    )
    assert last_cold_end < first_warm_start


@pytest.mark.asyncio
async def test_mode_barrier_defaults_to_running_one_scenario_at_a_time(tmp_path) -> None:
    # The suite reports latency. Concurrent scenarios contend for the same
    # local model and inflate the very number the benchmark exists to report,
    # so parallelism has to be opt-in.
    runner = _tracing_runner(tmp_path)
    grouped = _fake_grouped({"premium_direct": 3})

    assert runner.concurrency == 1

    await runner._run_groups(client=None, grouped=grouped, modes=["premium_direct"])

    events = [event for _, event in runner.trace]
    assert events == ["start", "end"] * 3


@pytest.mark.asyncio
async def test_mode_barrier_honours_a_raised_concurrency_bound(tmp_path) -> None:
    runner = _tracing_runner(tmp_path, concurrency=2)
    grouped = _fake_grouped({"premium_direct": 4})

    await runner._run_groups(client=None, grouped=grouped, modes=["premium_direct"])

    in_flight = peak = 0
    for _, event in runner.trace:
        in_flight += 1 if event == "start" else -1
        peak = max(peak, in_flight)
    assert peak == 2


@pytest.mark.asyncio
async def test_mode_barrier_keeps_results_in_dataset_order(tmp_path) -> None:
    # Under concurrency, completion order is arbitrary. The report's raw rows
    # are read by a human against the dataset, so they must not shuffle.
    runner = _tracing_runner(tmp_path, concurrency=4)
    grouped = _fake_grouped({"premium_direct": 4})

    results = await runner._run_groups(
        client=None, grouped=grouped, modes=["premium_direct"]
    )

    assert [result.scenario_id for result in results] == [
        f"premium_direct-{index}" for index in range(4)
    ]


@pytest.mark.asyncio
async def test_mode_barrier_publishes_earlier_modes_baselines_to_later_ones(tmp_path) -> None:
    runner = _tracing_runner(tmp_path, concurrency=4)
    grouped = _fake_grouped({"premium_direct": 2, "auto_simple_warm": 1})

    await runner._run_groups(
        client=None, grouped=grouped, modes=["premium_direct", "auto_simple_warm"]
    )

    assert runner.seen_baselines["auto_simple_warm-0"] != {}


@pytest.mark.asyncio
async def test_mode_barrier_hides_same_mode_baselines_so_results_do_not_depend_on_order(
    tmp_path,
) -> None:
    # A scenario reading a baseline written by a sibling in the same mode makes
    # the numbers depend on completion order, which under concurrency is not
    # even stable between runs of the same suite.
    runner = _tracing_runner(tmp_path, concurrency=4)
    grouped = _fake_grouped({"premium_direct": 3})

    await runner._run_groups(client=None, grouped=grouped, modes=["premium_direct"])

    assert all(seen == {} for seen in runner.seen_baselines.values())


# --- test-harness cache collections --------------------------------------------


def test_configured_app_deletes_the_cache_collection_it_created() -> None:
    # Every configured_app() gave itself a unique Qdrant collection and never
    # removed it. 774 of them had accumulated, 1.4 GB, all empty, and Qdrant
    # spent twenty minutes recovering them on every boot.
    from tests import support

    created: list[str] = []
    deleted: list[str] = []

    def record_delete(name: str) -> None:
        deleted.append(name)

    with support.configured_app(_collection_reaper=record_delete) as _:
        created.append(os.environ["NEBULA_SEMANTIC_CACHE_COLLECTION"])

    assert deleted == created
    assert created[0].startswith("nebula-test-cache-")


# --- degraded-run detection ----------------------------------------------------


def _health_payload(cache_state: str) -> dict:
    return {
        "status": "ready" if cache_state == "ready" else "degraded",
        "runtime_profile": "premium_first",
        "dependencies": {
            "gateway": {"status": "ready", "required": True},
            "semantic_cache": {"lifecycle_state": cache_state, "required": False},
            "local_ollama": {"lifecycle_state": "ready", "required": True},
        },
    }


def _health_client(payload: dict | None) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if payload is None:
            raise httpx.ConnectError("gateway unreachable")
        return httpx.Response(200, json=payload)

    return httpx.AsyncClient(
        base_url="http://127.0.0.1:8000", transport=httpx.MockTransport(handler)
    )


@pytest.mark.asyncio
async def test_the_report_records_the_dependency_health_it_probed(tmp_path) -> None:
    runner = _regression_runner(tmp_path)

    async with _health_client(_health_payload("ready")) as client:
        runner.runtime_health = await runner._probe_health(client)

    report = runner._build_report(_regression_results())

    assert report["runtime_health"]["status"] == "ready"


@pytest.mark.asyncio
async def test_a_run_with_an_unreachable_cache_is_marked_degraded(tmp_path) -> None:
    # This is the failure that already produced a wrong number twice: Qdrant
    # down, exit code 0, three scenarios quietly failing, and a savings
    # headline that reads exactly like a healthy run's.
    runner = _regression_runner(tmp_path)

    async with _health_client(_health_payload("not_ready")) as client:
        runner.runtime_health = await runner._probe_health(client)

    report = runner._build_report(_regression_results())
    rendered = runner._render_markdown(report)

    assert report["degraded_dependencies"] == ["semantic_cache"]
    assert "NOT COMPARABLE" in rendered
    assert "semantic_cache" in rendered


@pytest.mark.asyncio
async def test_a_healthy_run_carries_no_degradation_warning(tmp_path) -> None:
    runner = _regression_runner(tmp_path)

    async with _health_client(_health_payload("ready")) as client:
        runner.runtime_health = await runner._probe_health(client)

    rendered = runner._render_markdown(runner._build_report(_regression_results()))

    assert "NOT COMPARABLE" not in rendered
    assert report_degradation_free(rendered)


def report_degradation_free(rendered: str) -> bool:
    return "degraded" not in rendered.lower()


@pytest.mark.asyncio
async def test_a_failed_health_probe_is_recorded_not_swallowed(tmp_path) -> None:
    runner = _regression_runner(tmp_path)

    async with _health_client(None) as client:
        runner.runtime_health = await runner._probe_health(client)

    report = runner._build_report(_regression_results())

    assert report["runtime_health"]["probe"] == "failed"
    assert "NOT COMPARABLE" in runner._render_markdown(report)


def test_an_unprobed_report_makes_no_claim_either_way(tmp_path) -> None:
    # Unit tests build reports without a gateway. That must not manufacture a
    # warning, and must not manufacture a clean bill of health either.
    runner = _regression_runner(tmp_path)

    report = runner._build_report(_regression_results())

    assert report["runtime_health"]["probe"] == "not attempted"
    assert "NOT COMPARABLE" not in runner._render_markdown(report)
