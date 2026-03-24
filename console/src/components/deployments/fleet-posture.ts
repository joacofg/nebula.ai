import type { DeploymentRecord, EnrollmentState, FreshnessStatus } from "@/lib/admin-api";

export type BoundedActionStatus = "available" | "blocked" | "unavailable";

export type DeploymentPostureKind =
  | "pending_enrollment"
  | "linked"
  | "stale"
  | "offline"
  | "revoked"
  | "unlinked";

export type DeploymentPosture = {
  kind: DeploymentPostureKind;
  label: string;
  detail: string;
  isVisibleInHostedFleet: boolean;
  isBoundedActionBlocked: boolean;
};

export type BoundedActionAvailability = {
  status: BoundedActionStatus;
  isAvailable: boolean;
  disabledReason: string | null;
};

export type FleetPostureCounts = {
  total: number;
  linked: number;
  pendingEnrollment: number;
  stale: number;
  offline: number;
  revoked: number;
  unlinked: number;
  boundedActionBlocked: number;
};

export type DeploymentPostureDetails = {
  deployment: DeploymentRecord;
  posture: DeploymentPosture;
  boundedAction: BoundedActionAvailability;
};

export type FleetPostureSummary = {
  counts: FleetPostureCounts;
  deployments: DeploymentPostureDetails[];
};

const EMPTY_COUNTS: FleetPostureCounts = {
  total: 0,
  linked: 0,
  pendingEnrollment: 0,
  stale: 0,
  offline: 0,
  revoked: 0,
  unlinked: 0,
  boundedActionBlocked: 0,
};

function supportsRemoteCredentialRotation(deployment: DeploymentRecord) {
  return deployment.capability_flags.includes("remote_credential_rotation");
}

function getPendingPosture(): DeploymentPosture {
  return {
    kind: "pending_enrollment",
    label: "Pending enrollment",
    detail: "Hosted visibility remains pending enrollment until the deployment finishes linking.",
    isVisibleInHostedFleet: false,
    isBoundedActionBlocked: true,
  };
}

function getRevokedPosture(): DeploymentPosture {
  return {
    kind: "revoked",
    label: "Revoked",
    detail: "Hosted visibility is retained for audit context, but this link has been revoked.",
    isVisibleInHostedFleet: false,
    isBoundedActionBlocked: true,
  };
}

function getUnlinkedPosture(): DeploymentPosture {
  return {
    kind: "unlinked",
    label: "Unlinked",
    detail: "Hosted visibility is descriptive only because this deployment is no longer linked.",
    isVisibleInHostedFleet: false,
    isBoundedActionBlocked: true,
  };
}

function getActiveFreshnessPosture(status: FreshnessStatus | null): DeploymentPosture {
  if (status === "offline") {
    return {
      kind: "offline",
      label: "Offline visibility",
      detail: "Hosted posture is offline because the control plane has no current connectivity signal.",
      isVisibleInHostedFleet: true,
      isBoundedActionBlocked: true,
    };
  }

  if (status === "stale") {
    return {
      kind: "stale",
      label: "Stale visibility",
      detail: "Hosted posture is stale because the latest deployment report is older than the expected heartbeat window.",
      isVisibleInHostedFleet: true,
      isBoundedActionBlocked: true,
    };
  }

  return {
    kind: "linked",
    label: "Linked",
    detail: "Hosted posture reflects an active deployment link with current metadata visibility.",
    isVisibleInHostedFleet: true,
    isBoundedActionBlocked: false,
  };
}

export function getDeploymentPosture(deployment: DeploymentRecord): DeploymentPosture {
  switch (deployment.enrollment_state as EnrollmentState) {
    case "pending":
      return getPendingPosture();
    case "revoked":
      return getRevokedPosture();
    case "unlinked":
      return getUnlinkedPosture();
    case "active":
    default:
      return getActiveFreshnessPosture(deployment.freshness_status);
  }
}

export function getBoundedActionAvailability(
  deployment: DeploymentRecord,
): BoundedActionAvailability {
  if (deployment.enrollment_state !== "active") {
    if (deployment.enrollment_state === "revoked") {
      return {
        status: "unavailable",
        isAvailable: false,
        disabledReason: "Rotation is unavailable because this hosted link has been revoked.",
      };
    }

    if (deployment.enrollment_state === "unlinked") {
      return {
        status: "unavailable",
        isAvailable: false,
        disabledReason: "Rotation is unavailable because this deployment is no longer linked.",
      };
    }

    return {
      status: "unavailable",
      isAvailable: false,
      disabledReason: "Rotation is unavailable until this deployment finishes enrollment.",
    };
  }

  if (deployment.freshness_status === "stale") {
    return {
      status: "blocked",
      isAvailable: false,
      disabledReason:
        "Rotation is blocked because the deployment is stale and no longer trusted for remote changes.",
    };
  }

  if (deployment.freshness_status === "offline") {
    return {
      status: "blocked",
      isAvailable: false,
      disabledReason:
        "Rotation is blocked because the deployment is offline and cannot confirm credential handoff.",
    };
  }

  if (!supportsRemoteCredentialRotation(deployment)) {
    return {
      status: "unavailable",
      isAvailable: false,
      disabledReason:
        "Rotation is unavailable because this deployment did not advertise remote credential rotation support.",
    };
  }

  return {
    status: "available",
    isAvailable: true,
    disabledReason: null,
  };
}

export function getDeploymentPostureDetails(deployment: DeploymentRecord): DeploymentPostureDetails {
  const posture = getDeploymentPosture(deployment);
  const boundedAction = getBoundedActionAvailability(deployment);

  return {
    deployment,
    posture,
    boundedAction,
  };
}

export function summarizeFleetPosture(deployments: DeploymentRecord[]): FleetPostureSummary {
  const details = deployments.map(getDeploymentPostureDetails);
  const counts = details.reduce<FleetPostureCounts>((accumulator, detail) => {
    accumulator.total += 1;

    switch (detail.posture.kind) {
      case "linked":
        accumulator.linked += 1;
        break;
      case "pending_enrollment":
        accumulator.pendingEnrollment += 1;
        break;
      case "stale":
        accumulator.stale += 1;
        break;
      case "offline":
        accumulator.offline += 1;
        break;
      case "revoked":
        accumulator.revoked += 1;
        break;
      case "unlinked":
        accumulator.unlinked += 1;
        break;
    }

    if (!detail.boundedAction.isAvailable) {
      accumulator.boundedActionBlocked += 1;
    }

    return accumulator;
  }, { ...EMPTY_COUNTS });

  return {
    counts,
    deployments: details,
  };
}
