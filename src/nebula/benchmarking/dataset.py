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
