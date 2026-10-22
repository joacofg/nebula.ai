import json
from pathlib import Path

import pytest

from scripts import seed_demo_data
from scripts.demo_prepare import DEMO_QUALITY_TARGET, PREMIUM_MODELS, demo_policy
from scripts.seed_demo_data import DemoKeyRevokedError, demo_key_state, ensure_governance

REVOKED_AT = "2026-10-21T10:00:00Z"
CACHE_REPORT = Path(__file__).resolve().parents[1] / "benchmarks" / "cache" / "v1" / "report.json"
KEY_REVOKED_MESSAGE = (
    "La clave de demo fue revocada y su secreto no se puede reutilizar. "
    "Borrar .nebula/nebula.db, correr make migrate y volver a correr make demo."
)


def _key(name="acme-demo-key", tenant_id="acme-demo", revoked_at=None):
    return {"name": name, "tenant_id": tenant_id, "revoked_at": revoked_at}


class _Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body

    def raise_for_status(self):
        assert self.status_code < 400, f"unexpected {self.status_code}"


class _GatewayClient:
    """Answers the admin calls ensure_governance makes, for a tenant that already exists."""

    def __init__(self, keys):
        self.keys = keys
        self.posts = []

    def get(self, url, headers=None):
        if url.endswith("/api-keys"):
            return _Response(200, self.keys)
        return _Response(200, {})

    def post(self, url, headers=None, json=None):
        self.posts.append((url, json))
        return _Response(201, {})


def test_seed_finds_the_active_demo_key():
    assert demo_key_state([_key(name="other", tenant_id="other"), _key()]) == "active"


def test_seed_tells_a_revoked_demo_key_from_a_missing_one():
    assert demo_key_state([_key(revoked_at=REVOKED_AT)]) == "revoked"
    assert demo_key_state([]) == "missing"


def test_seed_prefers_an_active_demo_key_over_a_revoked_one():
    assert demo_key_state([_key(revoked_at=REVOKED_AT), _key()]) == "active"


def test_seed_ignores_a_key_with_the_demo_name_on_another_tenant():
    assert demo_key_state([_key(tenant_id="other")]) == "missing"


def test_seed_stops_with_an_actionable_message_when_the_demo_key_is_revoked():
    client = _GatewayClient([_key(revoked_at=REVOKED_AT)])

    with pytest.raises(DemoKeyRevokedError) as stopped:
        ensure_governance(client, require_key=True)

    assert str(stopped.value) == KEY_REVOKED_MESSAGE
    assert client.posts == []


def test_demo_prepare_path_warns_and_continues_when_the_demo_key_is_revoked(capsys):
    client = _GatewayClient([_key(revoked_at=REVOKED_AT)])

    ensure_governance(client, require_key=False)

    warning = [line for line in capsys.readouterr().out.splitlines() if "revocada" in line]
    assert len(warning) == 1
    assert client.posts == []


def test_seed_creates_the_demo_key_when_it_is_missing():
    client = _GatewayClient([])

    ensure_governance(client, require_key=True)

    assert [body["key"] for _, body in client.posts] == [seed_demo_data.DEMO_API_KEY]


def test_seed_leaves_an_active_demo_key_alone():
    client = _GatewayClient([_key()])

    ensure_governance(client, require_key=True)

    assert client.posts == []


def test_seed_main_exits_with_the_message_instead_of_a_traceback(monkeypatch, capsys):
    def revoked(client, *, require_key):
        raise DemoKeyRevokedError(KEY_REVOKED_MESSAGE)

    monkeypatch.setattr(seed_demo_data, "ensure_governance", revoked)

    assert seed_demo_data.main() == 1
    assert KEY_REVOKED_MESSAGE in capsys.readouterr().err


def test_sets_the_quality_target_the_three_example_prompts_are_tuned_for():
    policy = demo_policy({"routing_quality_target": 0.95, "allowed_premium_models": []})
    assert policy["routing_quality_target"] == DEMO_QUALITY_TARGET == 0.90


def test_adds_both_premium_models_to_a_non_empty_allowlist():
    policy = demo_policy({"routing_quality_target": 0.9, "allowed_premium_models": ["openai/gpt-4.1"]})
    assert policy["allowed_premium_models"] == ["openai/gpt-4.1", "anthropic/claude-haiku-4.5"]
    assert set(PREMIUM_MODELS) <= set(policy["allowed_premium_models"])


def test_leaves_an_empty_allowlist_empty_because_empty_allows_every_model():
    policy = demo_policy({"routing_quality_target": 0.9, "allowed_premium_models": []})
    assert policy["allowed_premium_models"] == []


def test_lifts_a_hard_budget_so_premium_is_not_blocked_mid_demo():
    policy = demo_policy(
        {
            "routing_quality_target": 0.9,
            "allowed_premium_models": [],
            "hard_budget_limit_usd": 0.01,
            "hard_budget_enforcement": "deny",
        }
    )
    assert policy["hard_budget_limit_usd"] is None
    assert policy["hard_budget_enforcement"] is None


def test_turns_the_semantic_cache_back_on_and_keeps_other_fields():
    policy = demo_policy(
        {
            "routing_quality_target": 0.9,
            "allowed_premium_models": [],
            "semantic_cache_enabled": False,
            "rate_limit_requests_per_minute": 60,
        }
    )
    assert policy["semantic_cache_enabled"] is True
    assert policy["rate_limit_requests_per_minute"] == 60


def test_sets_the_cache_threshold_the_measurement_registered_over_a_stale_stored_one():
    registered = json.loads(CACHE_REPORT.read_text(encoding="utf-8"))["preregistration"]["product_default_t"]

    policy = demo_policy(
        {
            "routing_quality_target": 0.9,
            "allowed_premium_models": [],
            "semantic_cache_similarity_threshold": 0.9,
        }
    )

    assert policy["semantic_cache_similarity_threshold"] == registered
