from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.router import cv, data, embed, frontier, knn, logreg, train


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _resp(pid, lang, cost):
    return {"prompt_id": pid, "lang": lang, "model": "m", "status": "ok", "text": "t",
            "finish_reason": "stop", "prompt_tokens": 1, "completion_tokens": 1,
            "cost_usd": cost, "resolved_model": "m", "error": ""}


def _tree(tmp_path, *, drop_cost=False):
    root = tmp_path / "gt"
    _write(root / "prompts.es.jsonl", [
        {"prompt_id": "code-0000", "task_type": "code", "source": "s", "prompt": "ES a",
         "role": "corpus", "en_subset": True},
        {"prompt_id": "code-0001", "task_type": "code", "source": "s", "prompt": "ES b",
         "role": "corpus", "en_subset": False},
    ])
    _write(root / "prompts.en.jsonl", [
        {"prompt_id": "code-0000", "task_type": "code", "source": "s", "prompt": "EN a",
         "role": "corpus", "en_subset": False},
        {"prompt_id": "code-0001", "task_type": "code", "source": "s", "prompt": "EN b",
         "role": "corpus", "en_subset": False},
    ])
    _write(root / "tiers.X.jsonl", [
        {"lang": "es", "prompt_id": "code-0000", "task_type": "code", "tier": "local",
         "local_substitutable": True, "economy_substitutable": True},
        {"lang": "es", "prompt_id": "code-0001", "task_type": "code", "tier": "frontier",
         "local_substitutable": False, "economy_substitutable": False},
        {"lang": "en", "prompt_id": "code-0000", "task_type": "code", "tier": "economy",
         "local_substitutable": False, "economy_substitutable": True},
    ])
    es_rows = [_resp("code-0000", "es", 0.1), _resp("code-0001", "es", 0.2)]
    if drop_cost:
        es_rows = es_rows[:1]
    _write(root / "responses" / "haiku.es.jsonl", es_rows)
    _write(root / "responses" / "gpt41.es.jsonl", [_resp("code-0000", "es", 1.0),
                                                   _resp("code-0001", "es", 2.0)])
    _write(root / "responses" / "haiku.en.jsonl", [_resp("code-0000", "en", 0.3)])
    _write(root / "responses" / "gpt41.en.jsonl", [_resp("code-0000", "en", 3.0)])
    return root


def test_load_examples_joins_prompts_labels_and_costs(tmp_path):
    got = data.load_examples(_tree(tmp_path), "tiers.X.jsonl")
    assert [(e.key, e.text, e.local_ok, e.economy_ok, e.cost_economy, e.cost_frontier)
            for e in got] == [
        ("en:code-0000", "EN a", False, True, 0.3, 3.0),
        ("es:code-0000", "ES a", True, True, 0.1, 1.0),
        ("es:code-0001", "ES b", False, False, 0.2, 2.0),
    ]


def test_load_examples_refuses_a_missing_cost(tmp_path):
    with pytest.raises(ValueError, match="cost"):
        data.load_examples(_tree(tmp_path, drop_cost=True), "tiers.X.jsonl")


def test_apply_prefix():
    assert embed.apply_prefix("hola", "none") == "hola"
    assert embed.apply_prefix("hola", "classification") == "classification: hola"


def _separable(n=200, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 2))
    y = (X[:, 0] - 0.5 * X[:, 1] > 0).astype(float)
    return X, y


def test_logreg_learns_a_separable_problem():
    X, y = _separable()
    w, b = logreg.fit(X, y, lam=0.1)
    assert w[0] > 0 and w[1] < 0
    assert ((logreg.predict(w, b, X) > 0.5) == (y == 1)).mean() > 0.9


def test_logreg_regularisation_shrinks_the_weights():
    X, y = _separable()
    small, _ = logreg.fit(X, y, lam=0.01)
    large, _ = logreg.fit(X, y, lam=100.0)
    assert np.linalg.norm(large) < np.linalg.norm(small)


def _ex(lang, pid, task):
    return data.Example(f"{lang}:{pid}", lang, pid, task, "t", True, True, 0.1, 1.0)


def _examples():
    out = []
    for task in ("code", "factual_qa"):
        for i in range(10):
            out.append(_ex("es", f"{task}-{i:04d}", task))
            if i < 4:
                out.append(_ex("en", f"{task}-{i:04d}", task))
    return out


def test_folds_keep_a_prompt_and_its_translation_together():
    ex = _examples()
    fold_of = cv.folds(ex, k=5, seed=1)
    assert fold_of == cv.folds(ex, k=5, seed=1)
    by_prompt = {}
    for e, f in zip(ex, fold_of):
        by_prompt.setdefault(e.prompt_id, set()).add(f)
    assert all(len(fs) == 1 for fs in by_prompt.values())
    for f in range(5):
        assert {e.task_type for e, g in zip(ex, fold_of) if g == f} == {"code", "factual_qa"}


def test_out_of_fold_never_trains_on_the_test_fold(monkeypatch):
    X, y = _separable(n=20)
    fold_of = [i % 4 for i in range(20)]
    seen = []
    real_fit = logreg.fit

    def spy(Xt, yt, lam, iters=50):
        seen.append(len(Xt))
        return real_fit(Xt, yt, lam, iters)

    monkeypatch.setattr(cv.logreg, "fit", spy)
    p = cv.out_of_fold(X, y, fold_of, lam=1.0)
    assert p.shape == (20,) and seen == [15, 15, 15, 15]


def test_choose_lambda_returns_a_grid_value_and_losses():
    X, y = _separable(n=60)
    lam, losses = cv.choose_lambda(X, y, [i % 5 for i in range(60)], grid=(0.1, 10.0))
    assert lam in (0.1, 10.0) and set(losses) == {0.1, 10.0}


def _e(local_ok, economy_ok, ce=0.1, cf=1.0, text="short", task="code", key="es:x"):
    return data.Example(key, "es", key.split(":")[1], task, text, local_ok, economy_ok, ce, cf)


def test_route_is_the_same_cascade_as_the_runtime():
    got = frontier.route(np.array([0.9, 0.2, 0.2]), np.array([0.1, 0.8, 0.1]), 0.5, 0.5)
    assert got == ["local", "economy", "frontier"]


def test_evaluate_counts_cost_and_quality():
    ex = [_e(True, True), _e(False, True, ce=0.2), _e(False, False, cf=2.0)]
    cost, quality = frontier.evaluate(["local", "economy", "frontier"], ex)
    assert cost == pytest.approx((0 + 0.2 + 2.0) / 3) and quality == pytest.approx(1.0)
    cost, quality = frontier.evaluate(["local", "local", "local"], ex)
    assert cost == 0 and quality == pytest.approx(1 / 3)


def test_pareto_drops_dominated_points_and_cost_at_quality():
    pts = [{"cost": 1.0, "quality": 0.9}, {"cost": 2.0, "quality": 0.8},
           {"cost": 0.5, "quality": 0.7}, {"cost": 3.0, "quality": 1.0}]
    front = frontier.pareto(pts)
    assert [p["cost"] for p in front] == [0.5, 1.0, 3.0]
    assert frontier.cost_at_quality(front, 0.85) == 1.0
    assert frontier.cost_at_quality(front, 1.01) is None


def test_heuristic_follows_the_gateway_rule():
    ex = [_e(True, True, text="hi"), _e(True, True, text="please analyze this"),
          _e(True, True, text="x" * 2100)]
    assert frontier.heuristic_tiers(ex) == ["local", "frontier", "frontier"]
    assert frontier.heuristic_tiers(ex, premium_tier="economy")[1] == "economy"


def test_oracle_is_perfect_and_no_dearer_than_frontier():
    ex = [_e(True, True), _e(False, True), _e(False, False)]
    corners = frontier.corner_points(ex)
    assert corners["oracle"][1] == pytest.approx(1.0)
    assert corners["oracle"][0] <= corners["all_frontier"][0]


def test_random_mixture_interpolates_between_corners():
    # economy is dominated (dearer than frontier here), so the hull is local<->frontier
    ex = [_e(True, False, ce=5.0, cf=1.0), _e(False, False, ce=5.0, cf=1.0)]
    # all-local: cost 0, quality 0.5; all-frontier: cost 1, quality 1
    assert frontier.random_cost_at_quality(ex, 0.75) == pytest.approx(0.5)
    assert frontier.random_cost_at_quality(ex, 0.4) == pytest.approx(0.0)


def test_knn_with_one_neighbour_copies_the_nearest_label():
    X = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0], [0.1, 0.9]])
    y = np.array([1.0, 1.0, 0.0, 0.0])
    p = knn.oof_probabilities(X, y, [0, 1, 0, 1], k=1)
    assert p.tolist() == [1.0, 1.0, 0.0, 0.0]


def test_choose_prefix_needs_a_clear_margin():
    assert train.choose_prefix({"none": 0.70, "classification": 0.71}) == "none"
    assert train.choose_prefix({"none": 0.70, "classification": 0.73}) == "classification"


def test_artifact_round_trips_through_the_runtime():
    from nebula.services.learned_router import LearnedRouterModel

    front = [{"tau_local": 0.6, "tau_economy": 0.4, "cost": 0.001, "quality": 0.9, "share": {}},
             {"tau_local": 0.8, "tau_economy": 0.5, "cost": 0.002, "quality": 0.95, "share": {}}]
    points = train.operating_points(front)
    assert points == [
        {"tau_local": 0.6, "tau_economy": 0.4, "quality": 0.9, "cost_per_prompt": 0.001},
        {"tau_local": 0.8, "tau_economy": 0.5, "quality": 0.95, "cost_per_prompt": 0.002},
    ]
    raw = train.artifact(
        weights={"local": (np.array([1.0, 2.0]), 0.5), "economy": (np.array([0.0, 1.0]), -0.5)},
        lambdas={"local": 1.0, "economy": 0.1}, prefix="none", points=points,
        labels={"file": "tiers.R3_ordinal_mean.jsonl", "sha256": "x"},
    )
    model = LearnedRouterModel.from_dict(json.loads(json.dumps(raw)))
    assert model.operating_point(0.93).tau_local == 0.8
    assert model.probabilities([0.0, 0.0])[0] == pytest.approx(1 / (1 + np.exp(-0.5)))


def test_latency_sample_is_balanced_and_summary_is_ordered():
    from scripts.ground_truth import records as gt_records
    from scripts.router import latency

    rows = [gt_records.PromptRow(f"{t}-{i:04d}", t, "s", "p", "corpus")
            for t in ("code", "factual_qa") for i in range(10)]
    got = latency.sample(rows, 6)
    assert [r.prompt_id for r in got] == ["code-0000", "code-0001", "code-0002",
                                          "factual_qa-0000", "factual_qa-0001", "factual_qa-0002"]
    s = latency.summarise([3.0, 1.0, 2.0])
    assert s["median_s"] == 2.0 and s["n"] == 3


def _toy_set(n=60, seed=3):
    rng = np.random.default_rng(seed)
    ex, X = [], []
    for i in range(n):
        x = rng.normal(size=4)
        ex.append(data.Example(f"es:t-{i:04d}", "es", f"t-{i:04d}", ("code", "factual_qa")[i % 2], "t",
                               bool(x[0] > 0), bool(x[1] > -0.5), 0.1, 1.0))
        X.append(x)
    return ex, np.array(X)


def test_nested_thresholds_are_chosen_without_the_test_fold():
    ex, X = _toy_set()
    fold_of = cv.folds(ex, k=3, seed=1)
    lambdas = {"local": 0.1, "economy": 0.1}
    everything = train.nested_tiers(ex, X, fold_of, lambdas, quality_target=1.01)
    cheapest = train.nested_tiers(ex, X, fold_of, lambdas, quality_target=0.0)
    assert everything == ["frontier"] * len(ex)
    assert set(cheapest) == {"local"}


def test_bootstrap_interval_brackets_the_point_estimate():
    ex, _ = _toy_set()
    tiers = ["local" if e.local_ok else "frontier" for e in ex]
    got = train.bootstrap_savings(ex, tiers, resamples=200, seed=5)
    low, high = got["vs_all_frontier_ci95"]
    assert low <= got["vs_all_frontier"] <= high
    assert got["quality"] == pytest.approx(1.0)
