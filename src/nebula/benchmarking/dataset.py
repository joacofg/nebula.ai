from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ScenarioMode = Literal[
    "premium_direct",
    "local_direct",
    "auto_simple_cold",
    "auto_simple_warm",
    "auto_complex",
    "auto_fallback",
]

SCENARIO_MODE_ORDER: tuple[ScenarioMode, ...] = (
    "premium_direct",
    "local_direct",
    "auto_simple_cold",
    "auto_simple_warm",
    "auto_complex",
    "auto_fallback",
)

PHASE5_COMPARISON_GROUPS: tuple[str, ...] = (
    "premium_control",
    "local_control",
    "auto_routing_cold",
    "auto_routing_warm_cache",
    "fallback_resilience",
    "premium_supporting_evidence",
)

PHASE5_COMPARISON_GROUP_METADATA: dict[str, dict[str, str]] = {
    "premium_control": {
        "label": "Premium control",
        "story_role": "Premium baseline for cost and latency comparison.",
    },
    "local_control": {
        "label": "Local control",
        "story_role": "Direct local execution proving avoided premium spend.",
    },
    "auto_routing_cold": {
        "label": "Auto-routing cold",
        "story_role": "Cold auto-routing behavior before cache reuse.",
    },
    "auto_routing_warm_cache": {
        "label": "Auto-routing warm cache",
        "story_role": "Warm-cache behavior showing low-latency repeat traffic.",
    },
    "fallback_resilience": {
        "label": "Fallback resilience",
        "story_role": "Forced local failure path proving the premium fallback story.",
    },
    "premium_supporting_evidence": {
        "label": "Supporting premium-routed evidence",
        "story_role": "Supporting evidence for premium-routed complex prompts without replacing the top-line five-group story.",
    },
}

SCENARIO_MODE_TO_COMPARISON_GROUP: dict[ScenarioMode, str] = {
    "premium_direct": "premium_control",
    "local_direct": "local_control",
    "auto_simple_cold": "auto_routing_cold",
    "auto_simple_warm": "auto_routing_warm_cache",
    "auto_complex": "premium_supporting_evidence",
    "auto_fallback": "fallback_resilience",
}


@dataclass(slots=True)
class ScenarioExpectation:
    route_target: str
    route_reason: str
    cache_hit: bool
    fallback_used: bool


@dataclass(slots=True)
class BenchmarkScenario:
    id: str
    mode: ScenarioMode
    messages: list[dict[str, object]]
    tags: list[str]
    expect: ScenarioExpectation


def comparison_group_for_mode(mode: ScenarioMode) -> str:
    return SCENARIO_MODE_TO_COMPARISON_GROUP[mode]


def load_scenarios(path: Path) -> list[BenchmarkScenario]:
    scenarios: list[BenchmarkScenario] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            expect = raw["expect"]
            scenarios.append(
                BenchmarkScenario(
                    id=raw["id"],
                    mode=raw["mode"],
                    messages=raw["messages"],
                    tags=raw["tags"],
                    expect=ScenarioExpectation(
                        route_target=expect["route_target"],
                        route_reason=expect["route_reason"],
                        cache_hit=expect["cache_hit"],
                        fallback_used=expect["fallback_used"],
                    ),
                )
            )
    return scenarios


def group_scenarios(scenarios: list[BenchmarkScenario]) -> dict[ScenarioMode, list[BenchmarkScenario]]:
    grouped: dict[ScenarioMode, list[BenchmarkScenario]] = {mode: [] for mode in SCENARIO_MODE_ORDER}
    for scenario in scenarios:
        grouped[scenario.mode].append(scenario)
    return grouped
