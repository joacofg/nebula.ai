from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.router import cv, data, embed, logreg


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
