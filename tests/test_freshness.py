"""Unit tests for compute_freshness thresholds and reason codes (D-08, D-09)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from nebula.services.heartbeat_ingest_service import compute_freshness


class TestComputeFreshness:
    def test_none_returns_none(self):
        """D-14: Pending deployments (never seen) return (None, None)."""
        status, reason = compute_freshness(None)
        assert status is None
        assert reason is None

    def test_connected_within_10_minutes(self):
        """Heartbeat 3 minutes ago is connected."""
        last_seen = datetime.now(UTC) - timedelta(minutes=3)
        status, reason = compute_freshness(last_seen)
        assert status == "connected"
        assert "ago" in reason

    def test_degraded_between_10_and_30_minutes(self):
        """Heartbeat 15 minutes ago is degraded."""
        last_seen = datetime.now(UTC) - timedelta(minutes=15)
        status, reason = compute_freshness(last_seen)
        assert status == "degraded"
        assert "No heartbeat for" in reason

    def test_stale_between_30_and_60_minutes(self):
        """Heartbeat 45 minutes ago is stale."""
        last_seen = datetime.now(UTC) - timedelta(minutes=45)
        status, reason = compute_freshness(last_seen)
        assert status == "stale"
        assert "No heartbeat for" in reason

    def test_offline_over_60_minutes(self):
        """Heartbeat 2 hours ago is offline."""
        last_seen = datetime.now(UTC) - timedelta(hours=2)
        status, reason = compute_freshness(last_seen)
        assert status == "offline"
        assert "No heartbeat since" in reason

    def test_clock_skew_clamped(self):
        """Future timestamp (clock skew) should clamp to connected, not error."""
        future = datetime.now(UTC) + timedelta(minutes=5)
        status, reason = compute_freshness(future)
        assert status == "connected"

    def test_freshness_boundary_connected_just_under_10min(self):
        """9 minutes 59 seconds ago is still connected (just under boundary)."""
        last_seen = datetime.now(UTC) - timedelta(minutes=9, seconds=59)
        status, _ = compute_freshness(last_seen)
        assert status == "connected"

    def test_freshness_boundary_degraded_at_10min_1sec(self):
        """10 minutes and 1 second ago crosses into degraded."""
        last_seen = datetime.now(UTC) - timedelta(minutes=10, seconds=1)
        status, _ = compute_freshness(last_seen)
        assert status == "degraded"

    def test_reason_codes_time_based_only(self):
        """D-09: Reason codes must be time-based only, no inferred cause words."""
        forbidden = ["healthy", "running", "stable", "connection", "network"]
        for delta_min in [3, 15, 45]:
            last_seen = datetime.now(UTC) - timedelta(minutes=delta_min)
            _, reason = compute_freshness(last_seen)
            for word in forbidden:
                assert word not in reason.lower(), (
                    f"Reason '{reason}' contains forbidden word '{word}'"
                )
