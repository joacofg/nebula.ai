from scripts.demo_prepare import DEMO_QUALITY_TARGET, PREMIUM_MODELS, demo_policy


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
