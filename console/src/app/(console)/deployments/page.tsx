"use client";

import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import {
  ADMIN_DEPLOYMENTS_ENDPOINT,
  createDeployment,
  generateEnrollmentToken,
  listDeployments,
  revokeDeployment,
  unlinkDeployment,
  type DeploymentCreateInput,
  type DeploymentRecord,
  type EnrollmentTokenResponse,
} from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { queryKeys } from "@/lib/query-keys";
import { getHostedContractContent } from "@/lib/hosted-contract";
import { CreateDeploymentSlotDrawer } from "@/components/deployments/create-deployment-slot-drawer";
import { DeploymentDetailDrawer } from "@/components/deployments/deployment-detail-drawer";
import { DeploymentTable } from "@/components/deployments/deployment-table";
import { EnrollmentTokenRevealDialog } from "@/components/deployments/enrollment-token-reveal-dialog";
import { FleetPostureSummary } from "@/components/deployments/fleet-posture-summary";
import { RevokeConfirmationDialog } from "@/components/deployments/revoke-confirmation-dialog";
import { UnlinkConfirmationDialog } from "@/components/deployments/unlink-confirmation-dialog";

type DrawerState =
  | { mode: "create" }
  | { mode: "detail"; deployment: DeploymentRecord };

export default function DeploymentsPage() {
  const queryClient = useQueryClient();
  const { adminKey } = useAdminSession();
  const { reinforcement } = getHostedContractContent();

  const [drawerState, setDrawerState] = useState<DrawerState>({ mode: "create" });
  const [selectedDeploymentId, setSelectedDeploymentId] = useState<string | null>(null);

  // Token reveal dialog state
  const [tokenDialogOpen, setTokenDialogOpen] = useState(false);
  const [pendingToken, setPendingToken] = useState<EnrollmentTokenResponse | null>(null);

  // Confirmation dialog states
  const [revokeTargetId, setRevokeTargetId] = useState<string | null>(null);
  const [unlinkTargetId, setUnlinkTargetId] = useState<string | null>(null);

  const deploymentsQuery = useQuery({
    queryKey: queryKeys.deployments,
    queryFn: () => listDeployments(adminKey ?? ""),
    enabled: Boolean(adminKey),
  });

  const createMutation = useMutation({
    mutationFn: async (payload: DeploymentCreateInput) => {
      if (!adminKey) throw new Error("Operator session missing.");
      return createDeployment(adminKey, payload);
    },
    onSuccess: async (deployment) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.deployments });
      // After creating, immediately generate a token
      if (adminKey) {
        const tokenResp = await generateEnrollmentToken(adminKey, deployment.id);
        setPendingToken(tokenResp);
        setTokenDialogOpen(true);
      }
      setSelectedDeploymentId(deployment.id);
      setDrawerState({ mode: "detail", deployment });
    },
  });

  const generateTokenMutation = useMutation({
    mutationFn: async (deploymentId: string) => {
      if (!adminKey) throw new Error("Operator session missing.");
      return generateEnrollmentToken(adminKey, deploymentId);
    },
    onSuccess: async (tokenResp) => {
      setPendingToken(tokenResp);
      setTokenDialogOpen(true);
      await queryClient.invalidateQueries({ queryKey: queryKeys.deployments });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: async (deploymentId: string) => {
      if (!adminKey) throw new Error("Operator session missing.");
      return revokeDeployment(adminKey, deploymentId);
    },
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.deployments });
      setRevokeTargetId(null);
      setDrawerState({ mode: "detail", deployment: updated });
    },
  });

  const unlinkMutation = useMutation({
    mutationFn: async (deploymentId: string) => {
      if (!adminKey) throw new Error("Operator session missing.");
      return unlinkDeployment(adminKey, deploymentId);
    },
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.deployments });
      setUnlinkTargetId(null);
      setDrawerState({ mode: "detail", deployment: updated });
    },
  });

  // Keep detail drawer in sync with refreshed data
  const selectedDeployment =
    drawerState.mode === "detail"
      ? (deploymentsQuery.data?.find((d) => d.id === drawerState.deployment.id) ??
        drawerState.deployment)
      : null;

  return (
    <section className="space-y-6">
      <header className="panel flex flex-col gap-4 px-6 py-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
            Deployments
          </div>
          <h2 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
            Deployment management
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Manage linked self-hosted Nebula deployments through{" "}
            <span className="font-[var(--font-fira-code)]">{ADMIN_DEPLOYMENTS_ENDPOINT}</span>.
          </p>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            {reinforcement.operatorReadingGuidance[2]} {reinforcement.allowedDescriptiveClaims[4]}
          </p>
        </div>
        <button
          type="button"
          className="action-button gap-2"
          onClick={() => setDrawerState({ mode: "create" })}
        >
          <Plus className="h-4 w-4" />
          Create deployment slot
        </button>
      </header>

      <div className="space-y-6">
        {deploymentsQuery.isLoading ? (
          <div className="panel px-6 py-8 text-sm text-slate-500">
            Loading deployment inventory...
          </div>
        ) : deploymentsQuery.isError ? (
          <div className="panel border-rose-200 bg-rose-50 px-6 py-8 text-sm text-rose-900">
            {deploymentsQuery.error instanceof Error
              ? deploymentsQuery.error.message
              : "Unable to load deployments."}
          </div>
        ) : (
          <>
            <FleetPostureSummary deployments={deploymentsQuery.data ?? []} />

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.95fr)]">
              <div>
                <DeploymentTable
                  deployments={deploymentsQuery.data ?? []}
                  selectedDeploymentId={selectedDeploymentId}
                  onSelectDeployment={(deployment) => {
                    setSelectedDeploymentId(deployment.id);
                    setDrawerState({ mode: "detail", deployment });
                  }}
                />
              </div>

              {drawerState.mode === "create" ? (
                <CreateDeploymentSlotDrawer
                  isSaving={createMutation.isPending}
                  onClose={() => {
                    if (selectedDeployment) {
                      setDrawerState({ mode: "detail", deployment: selectedDeployment });
                    }
                  }}
                  onSubmit={async (payload) => {
                    await createMutation.mutateAsync(payload);
                  }}
                />
              ) : (
                <DeploymentDetailDrawer
                  deployment={selectedDeployment ?? drawerState.deployment}
                  isGeneratingToken={generateTokenMutation.isPending}
                  onGenerateToken={(deploymentId) => generateTokenMutation.mutate(deploymentId)}
                  onRequestRevoke={(deploymentId) => setRevokeTargetId(deploymentId)}
                  onRequestUnlink={(deploymentId) => setUnlinkTargetId(deploymentId)}
                  onClose={() => setDrawerState({ mode: "create" })}
                />
              )}
            </div>
          </>
        )}
      </div>

      <EnrollmentTokenRevealDialog
        tokenResponse={pendingToken}
        open={tokenDialogOpen}
        onClose={() => {
          setTokenDialogOpen(false);
          setPendingToken(null);
        }}
      />

      <RevokeConfirmationDialog
        open={revokeTargetId !== null}
        isRevoking={revokeMutation.isPending}
        onConfirm={() => {
          if (revokeTargetId) revokeMutation.mutate(revokeTargetId);
        }}
        onDismiss={() => setRevokeTargetId(null)}
      />

      <UnlinkConfirmationDialog
        open={unlinkTargetId !== null}
        isUnlinking={unlinkMutation.isPending}
        onConfirm={() => {
          if (unlinkTargetId) unlinkMutation.mutate(unlinkTargetId);
        }}
        onDismiss={() => setUnlinkTargetId(null)}
      />
    </section>
  );
}
