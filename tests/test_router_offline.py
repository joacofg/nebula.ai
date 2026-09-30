from __future__ import annotations

import json

import pytest

from scripts.router import data, embed


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
