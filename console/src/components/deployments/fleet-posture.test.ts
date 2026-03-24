import { describe, expect, it } from "vitest";

import {
  getBoundedActionAvailability,
  getDeploymentPosture,
  summarizeFleetPosture,
} from "@/components/deployments/fleet-posture";
import type { DeploymentRecord } from "@/lib/admin-api";

const baseDeployment: DeploymentRecord = {
  id: "dep-1",
  display_name: "Production Gateway",
  environment: "production",
  enrollment_state: "active",
  nebula_version: "2.0.0",
  capability_flags: ["remote_credential_rotation"],
  enrolled_at: "2026-03-22T12:00:00Z",
  revoked_at: null,
  unlinked_at: null,
  created_at: "2026-03-22T11:00:00Z",
  updated_at: "2026-03-22T12:00:00Z",
  last_seen_at: "2026-03-22T12:10:00Z",
  freshness_status: "connected",
  freshness_reason: "Heartbeat received recently",
  dependency_summary: { healthy: ["gateway"], degraded: [], unavailable: [] },
  remote_action_summary: { queued: 0, applied: 0, failed: 0, last_action_at: null },
};

describe("fleet-posture", () => {
  it("summarizes mixed fleets into posture counts from deployment metadata", () => {
    const deployments: DeploymentRecord[] = [
      baseDeployment,
      { ...baseDeployment, id: "dep-2", display_name: "Pending", enrollment_state: "pending", freshness_status: null },
      { ...baseDeployment, id: "dep-3", display_name: "Stale", freshness_status: "stale" },
      { ...baseDeployment, id: "dep-4", display_name: "Offline", freshness_status: "offline" },
      { ...baseDeployment, id: "dep-5", display_name: "Revoked", enrollment_state: "revoked" },
      { ...baseDeployment, id: "dep-6", display_name: "Unlinked", enrollment_state: "unlinked" },
      { ...baseDeployment, id: "dep-7", display_name: "Unsupported", capability_flags: [] },
    ];

    const summary = summarizeFleetPosture(deployments);

    expect(summary.counts).toEqual({
      total: 7,
      linked: 2,
      pendingEnrollment: 1,
      stale: 1,
      offline: 1,
      revoked: 1,
      unlinked: 1,
      boundedActionBlocked: 6,
    });
  });

  it("treats pending enrollment with null freshness as pending rather than stale or offline", () => {
    const posture = getDeploymentPosture({
      ...baseDeployment,
      enrollment_state: "pending",
      freshness_status: null,
      last_seen_at: null,
    });

    expect(posture.kind).toBe("pending_enrollment");
    expect(posture.label).toBe("Pending enrollment");
    expect(posture.detail).toContain("pending enrollment");
  });

  it("groups stale and offline active deployments into distinct visibility states", () => {
    const stalePosture = getDeploymentPosture({
      ...baseDeployment,
      freshness_status: "stale",
    });
    const offlinePosture = getDeploymentPosture({
      ...baseDeployment,
      freshness_status: "offline",
    });

    expect(stalePosture.kind).toBe("stale");
    expect(stalePosture.label).toBe("Stale visibility");
    expect(stalePosture.isVisibleInHostedFleet).toBe(true);

    expect(offlinePosture.kind).toBe("offline");
    expect(offlinePosture.label).toBe("Offline visibility");
    expect(offlinePosture.isVisibleInHostedFleet).toBe(true);
  });

  it("derives fail-closed bounded action reasons for pending, stale, offline, revoked, unlinked, and unsupported deployments", () => {
    const cases: Array<{
      deployment: DeploymentRecord;
      status: "blocked" | "unavailable";
      reason: string;
    }> = [
      {
        deployment: { ...baseDeployment, enrollment_state: "pending", freshness_status: null },
        status: "unavailable",
        reason: "Rotation is unavailable until this deployment finishes enrollment.",
      },
      {
        deployment: { ...baseDeployment, freshness_status: "stale" },
        status: "blocked",
        reason:
          "Rotation is blocked because the deployment is stale and no longer trusted for remote changes.",
      },
      {
        deployment: { ...baseDeployment, freshness_status: "offline" },
        status: "blocked",
        reason:
          "Rotation is blocked because the deployment is offline and cannot confirm credential handoff.",
      },
      {
        deployment: { ...baseDeployment, enrollment_state: "revoked" },
        status: "unavailable",
        reason: "Rotation is unavailable because this hosted link has been revoked.",
      },
      {
        deployment: { ...baseDeployment, enrollment_state: "unlinked" },
        status: "unavailable",
        reason: "Rotation is unavailable because this deployment is no longer linked.",
      },
      {
        deployment: { ...baseDeployment, capability_flags: [] },
        status: "unavailable",
        reason:
          "Rotation is unavailable because this deployment did not advertise remote credential rotation support.",
      },
    ];

    for (const testCase of cases) {
      expect(getBoundedActionAvailability(testCase.deployment)).toEqual({
        status: testCase.status,
        isAvailable: false,
        disabledReason: testCase.reason,
      });
    }

    expect(getBoundedActionAvailability(baseDeployment)).toEqual({
      status: "available",
      isAvailable: true,
      disabledReason: null,
    });
  });
});
