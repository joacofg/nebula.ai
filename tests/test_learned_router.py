from __future__ import annotations

import math

import pytest

from nebula.services.learned_router import ALL_FRONTIER, LearnedRouterModel, OperatingPoint, tier_for


def _raw(points=None):
    return {
        "version": 1,
        "embedding_model": "nomic-embed-text",
        "prefix": "none",
        "models": {
            "local": {"weights": [2.0, 0.0], "bias": 0.0},
            "economy": {"weights": [0.0, 2.0], "bias": 0.0},
        },
        "operating_points": points or [
            {"tau_local": 0.5, "tau_economy": 0.5, "quality": 0.80, "cost_per_prompt": 0.001},
            {"tau_local": 0.7, "tau_economy": 0.5, "quality": 0.90, "cost_per_prompt": 0.002},
            {"tau_local": 0.9, "tau_economy": 0.9, "quality": 0.95, "cost_per_prompt": 0.004},
        ],
    }


def test_probabilities_are_the_logistic_of_each_score():
    model = LearnedRouterModel.from_dict(_raw())
    p_local, p_economy = model.probabilities([1.0, -1.0])
    assert p_local == pytest.approx(1 / (1 + math.exp(-2.0)))
    assert p_economy == pytest.approx(1 / (1 + math.exp(2.0)))


def test_tier_cascade():
    point = OperatingPoint(0.5, 0.6, 0.9, 0.01)
    assert tier_for(0.7, 0.1, point) == "local"
    assert tier_for(0.4, 0.6, point) == "economy"
    assert tier_for(0.4, 0.5, point) == "frontier"


def test_operating_point_is_the_cheapest_that_meets_the_target():
    model = LearnedRouterModel.from_dict(_raw())
    assert model.operating_point(0.85).tau_local == 0.7
    assert model.operating_point(0.80).tau_local == 0.5


def test_a_target_above_every_point_routes_everything_to_frontier():
    model = LearnedRouterModel.from_dict(_raw())
    assert model.operating_point(0.99) is ALL_FRONTIER
    assert model.choose([10.0, 10.0], 0.99).tier == "frontier"


def test_choose_reports_probabilities_and_point():
    choice = LearnedRouterModel.from_dict(_raw()).choose([3.0, 0.0], 0.8)
    assert choice.tier == "local" and choice.p_local > 0.99 and choice.point.quality == 0.8


def test_dimension_mismatch_and_bad_artifacts_are_refused():
    model = LearnedRouterModel.from_dict(_raw())
    with pytest.raises(ValueError, match="dimension"):
        model.probabilities([1.0])
    with pytest.raises(ValueError, match="version"):
        LearnedRouterModel.from_dict({**_raw(), "version": 2})
    with pytest.raises(ValueError, match="operating"):
        LearnedRouterModel.from_dict({**_raw(), "operating_points": []})


def test_the_packaged_v1_artifact_loads_and_matches_nomic():
    from nebula.core.config import Settings

    model = LearnedRouterModel.from_file(Settings().learned_router_path)
    assert model.dimension == 768 and model.embedding_model == "nomic-embed-text"
    assert model.operating_point(0.95).quality >= 0.95


def test_a_perfect_quality_target_always_means_all_frontier():
    from nebula.core.config import Settings

    model = LearnedRouterModel.from_file(Settings().learned_router_path)
    assert model.operating_point(1.0) is ALL_FRONTIER
    assert LearnedRouterModel.from_dict(_raw([
        {"tau_local": 0.9, "tau_economy": 0.9, "quality": 1.0, "cost_per_prompt": 0.001}
    ])).operating_point(1.0) is ALL_FRONTIER
