from __future__ import annotations

from pathlib import Path

from nebula.benchmarking.dataset import SCENARIO_MODE_ORDER, group_scenarios, load_scenarios
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

    assert report["summary"]["total_requests"] == 2
    assert report["summary"]["route_distribution"]["local"] == 1
    assert report["summary"]["route_distribution"]["premium"] == 1
    assert report["summary"]["fallback_rate"] == 0.5
    assert "auto-fallback-hello" in report["summary"]["scenario_failures"]
    assert "# Nebula Benchmark Report" in markdown
    assert "| local-direct-brief |" in markdown
