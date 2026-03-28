from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from nebula.benchmarking.dataset import (
    PHASE5_COMPARISON_GROUPS,
    SCENARIO_MODE_ORDER,
    comparison_group_for_mode,
    group_scenarios,
    load_scenarios,
)
from nebula.benchmarking.pricing import PricingCatalog
from nebula.benchmarking.run import BenchmarkResult, BenchmarkRunner
from nebula.providers.base import CompletionUsage


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
            response_preview="premium",
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
            response_preview="local",
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
            response_preview="cold",
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
            response_preview="warm",
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
            response_preview="complex",
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
            response_preview=None,
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
        await runner._run_scenario(client=client, scenario=scenario, prompt_baselines={})

    assert captured_headers["X-Nebula-API-Key"] == runner.settings.bootstrap_api_key
    assert captured_headers["X-Nebula-Tenant-ID"] == runner.settings.bootstrap_tenant_id
